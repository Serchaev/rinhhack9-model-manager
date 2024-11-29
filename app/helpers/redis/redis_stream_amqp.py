import asyncio
import logging
import traceback
from typing import Any, AsyncGenerator, Union
from uuid import uuid4

import async_timeout
from redis import ConnectionError, ResponseError
from redis.asyncio import Redis
from tenacity import retry, wait_random

from app.helpers.asyncio_utils import run_in_executor
from app.helpers.redis.redis_amqp_abc import MessageRedisAbc, RedisAmqpAbc


class RedisStreamAmqp(RedisAmqpAbc):
    def __init__(
        self,
        redis: Redis,
        logger: logging.Logger = None,
        group_name: str = "default",
        consumer_name: str = None,
        listening_periodicity: float = 0.01,
        timeout: int = 10,
        noack: bool = False,
        **kwargs,
    ):
        self.group_name = group_name
        self.consumer_name = consumer_name or str(uuid4())
        self.queues_extra = {}
        self.noack = noack
        super().__init__(redis, logger, listening_periodicity, timeout, **kwargs)

    async def init_queue(self, routing_key: str, **kwargs):
        self.queues_extra[routing_key] = kwargs or {}
        try:
            await self.redis.xgroup_create(
                routing_key, self.group_name, mkstream=True, **self.queues_extra[routing_key]
            )
            self.logger.info("Инициализация очереди %s прошла успешно", routing_key)
        except ResponseError:
            self.logger.info("Очередь %s уже существует", routing_key)

    async def send(
        self, message: Union[str, bytes, list, dict], routing_key: str, max_len: int = 1000, **kwargs
    ) -> None:
        await self.redis.xadd(routing_key, message, maxlen=max_len)
        self.logger.debug("Отправка сообщения в очередь %s прошла успешно", routing_key)
        message_count = await self.redis.xlen(routing_key)
        if message_count >= max_len:
            self.logger.warning("Очередь %s переполнена", routing_key)

    async def init_consumer(self, routing_key: str, on_message: callable, **kwargs) -> None:
        asyncio.create_task(retry(wait=wait_random(min=1, max=10))(self.consumer_callback)(routing_key, on_message))
        self.logger.info("Инициализация слушателя очереди %s прошла успешно", routing_key)

    async def _get_message(self, routing_key: str, **kwargs):
        try:
            async with async_timeout.timeout(self.timeout):
                message = await self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={routing_key: ">"},
                    **kwargs,
                )
                return message
        except ConnectionError as error:
            self.logger.error("Ошибка подключения к Redis, reasons: %s", error)
            raise error
        except asyncio.TimeoutError:
            self.logger.warning("Превышено время ожидания сообщения из Redis")
        except ResponseError:
            self.logger.warning("Очереди %s не найдено в Redis", routing_key)
            await self.init_queue(routing_key, **self.queues_extra.get(routing_key, {}))

    async def get_message(self, routing_key: str, **kwargs) -> Any:
        while True:
            message = await self._get_message(routing_key, count=1, **kwargs)
            if message:
                [[_stream, [[message_id, data]]]] = message
                await self.redis.xack(routing_key, self.group_name, message_id)
                await self.redis.xdel(routing_key, message_id)
                return data
            await asyncio.sleep(self.listening_periodicity)

    async def get_messages(self, routing_key: str, batch_size: int = 1, **kwargs) -> list:
        while True:
            messages = await self._get_message(routing_key, count=batch_size, **kwargs)
            if messages:
                message_ids = []
                result = []
                for _stream, entries in messages:
                    for message_id, data in entries:
                        message_ids.append(message_id)
                        result.append(data)
                await self.redis.xack(routing_key, self.group_name, *message_ids)
                await self.redis.xdel(routing_key, *message_ids)
                return result

            await asyncio.sleep(self.listening_periodicity)


class MessageRedisStream(MessageRedisAbc):
    def __init__(
        self,
        redis: Redis,
        message_id: Any,
        body: Any,
        rollback_on_error: bool,
        routing_key: str,
        group_name: str,
        noack: bool = False,
        logger: logging.Logger = logging,
        **kwargs,
    ):
        self.message_id = message_id
        self.group_name = group_name
        super().__init__(redis, routing_key, body, noack, rollback_on_error, logger, **kwargs)

    async def delete(self):
        await self.redis.xdel(self.routing_key, self.message_id)
        self.logger.debug("MessageRedisStream :: сообщение удалено")

    async def ack(self):
        await self.redis.xack(self.routing_key, self.group_name, self.message_id)
        self.logger.debug("MessageRedisStream :: сообщение подтверждено")

    async def rollback(self):
        await self.redis.xadd(self.routing_key, self.body)
        self.logger.debug("MessageRedisStream :: сообщение возвращено обратно в очередь")


class RedisStreamShieldAmqp(RedisStreamAmqp):
    async def consumer_callback(self, routing_key: str, on_message: callable):
        """
        Слушатель сообщений из очереди
        :param routing_key:             название очереди
        :param on_message:              callback получения сообщения
        """
        while True:
            message: MessageRedisAbc = await self.get_message(routing_key)
            self.logger.debug("Обработка сообщения из очереди %s...", routing_key)
            try:
                if asyncio.iscoroutinefunction(on_message):
                    await on_message(message)
                else:
                    await run_in_executor(message, executor=None, loop=self.loop, func=on_message)
                self.logger.debug("Обработка сообщения из очереди %s прошла успешно", routing_key)
            except:  # noqa
                self.logger.error("Ошибка при обработки сообщения из очереди %s", routing_key)
                self.logger.error(traceback.format_exc())
                raise

    async def _get_message(self, routing_key: str, **kwargs):
        try:
            async with async_timeout.timeout(self.timeout):
                message = await self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={routing_key: ">"},
                    noack=self.noack,
                    **kwargs,
                )
                return message
        except ConnectionError as error:
            self.logger.error("Ошибка подключения к Redis, reasons: %s", error)
            raise error
        except asyncio.TimeoutError:
            self.logger.warning("Превышено время ожидания сообщения из Redis")
        except ResponseError:
            self.logger.warning("Очереди %s не найдено в Redis", routing_key)
            await self.init_queue(routing_key, **self.queues_extra.get(routing_key, {}))

    async def get_message(self, routing_key: str, **kwargs) -> Any:
        while True:
            message = await self._get_message(routing_key, count=1, **kwargs)
            if message:
                [[_stream, [[message_id, data]]]] = message
                return MessageRedisStream(
                    redis=self.redis,
                    message_id=message_id,
                    body=data,
                    noack=self.noack,
                    rollback_on_error=True,
                    routing_key=routing_key,
                    group_name=self.group_name,
                )
            await asyncio.sleep(self.listening_periodicity)

    async def get_messages(
        self, routing_key: str, batch_size: int = 1, **kwargs
    ) -> AsyncGenerator[MessageRedisAbc, None]:
        while True:
            messages = await self._get_message(routing_key, count=batch_size, **kwargs)
            if messages:
                for _stream, entries in messages:
                    for message_id, data in entries:
                        handled_message = MessageRedisStream(
                            redis=self.redis,
                            message_id=message_id,
                            body=data,
                            noack=self.noack,
                            rollback_on_error=self.rollback_on_error,
                            routing_key=routing_key,
                            group_name=self.group_name,
                        )
                        yield handled_message
                return

            await asyncio.sleep(self.listening_periodicity)
