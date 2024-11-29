import asyncio
import logging
import traceback
from typing import Any, AsyncGenerator, Union

import async_timeout
from redis import ConnectionError
from redis.asyncio import Redis
from tenacity import retry, wait_random

from app.helpers.asyncio_utils import run_in_executor
from app.helpers.redis.redis_amqp_abc import MessageRedisAbc, RedisAmqpAbc


class RedisQueueAmqp(RedisAmqpAbc):
    def __init__(
        self,
        redis: Redis = None,
        logger: logging.Logger = logging,
        listening_periodicity: float = 0.01,
        timeout: int = 10,
        **kwargs,
    ):
        super().__init__(redis, logger, listening_periodicity, timeout, **kwargs)

    async def init_queue(self, routing_key: str, **kwargs) -> None:
        """
        Инициализация очереди
        :param routing_key:         название очереди
        :param kwargs:              дополнительные параметры
        :return:                    None
        """
        return

    async def send(self, message: Union[str, bytes, list, dict], routing_key: str, **kwargs) -> None:
        await self.redis.rpush(routing_key, message)
        self.logger.debug("Отправка сообщения в очередь %s прошла успешно", routing_key)

    async def init_consumer(self, routing_key: str, on_message: callable, **kwargs) -> None:
        asyncio.create_task(retry(wait=wait_random(min=1, max=10))(self.consumer_callback)(routing_key, on_message))
        self.logger.info("Инициализация слушателя очереди %s прошла успешно", routing_key)

    async def get_message(self, routing_key: str) -> Any:
        while True:
            try:
                async with async_timeout.timeout(self.timeout):
                    message = await self.redis.lpop(routing_key)
            except ConnectionError as error:
                self.logger.error("Ошибка подключения к Redis, reasons: %s", error)
                raise error
            except asyncio.TimeoutError:
                self.logger.warning("Превышено время ожидания сообщения из Redis")
                continue
            if message:
                return message
            await asyncio.sleep(self.listening_periodicity)


class MessageRedisQueue(MessageRedisAbc):
    def __init__(
        self,
        redis: Redis,
        body: Any,
        rollback_on_error: bool,
        routing_key: str,
        noack: bool = False,
        logger: logging.Logger = logging,
        **kwargs,
    ):
        super().__init__(redis, routing_key, body, noack, rollback_on_error, logger, **kwargs)

    async def delete(self):
        return

    async def ack(self):
        return

    async def rollback(self):
        await self.redis.lpush(self.routing_key, self.body)
        self.logger.debug("MessageRedisQueue :: сообщение возвращено обратно в очередь")


class RedisQueueShieldAmqp(RedisQueueAmqp):
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

    async def get_message(self, routing_key: str) -> Any:
        while True:
            try:
                async with async_timeout.timeout(self.timeout):
                    message = await self.redis.lpop(routing_key)
            except ConnectionError as error:
                self.logger.error("Ошибка подключения к Redis, reasons: %s", error)
                raise error
            except asyncio.TimeoutError:
                self.logger.warning("Превышено время ожидания сообщения из Redis")
                continue
            if message:
                return MessageRedisQueue(
                    redis=self.redis, body=message, rollback_on_error=True, routing_key=routing_key
                )
            await asyncio.sleep(self.listening_periodicity)

    async def get_messages(
        self, routing_key: str, batch_size: int = 1, **kwargs
    ) -> AsyncGenerator[MessageRedisAbc, None]:
        while True:
            try:
                async with async_timeout.timeout(self.timeout):
                    messages = await self.redis.lpop(routing_key, count=batch_size, **kwargs)
            except ConnectionError as error:
                self.logger.error("Ошибка подключения к Redis, reasons: %s", error)
                raise error
            except asyncio.TimeoutError:
                self.logger.warning("Превышено время ожидания сообщения из Redis")
                continue
            if messages:
                for message in messages:
                    handled_message = MessageRedisQueue(
                        redis=self.redis, body=message, rollback_on_error=True, routing_key=routing_key
                    )
                    yield handled_message
                return

            await asyncio.sleep(self.listening_periodicity)
