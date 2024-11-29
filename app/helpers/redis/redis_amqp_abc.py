import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from typing import Any

from redis.asyncio import Redis

from app.helpers.interfaces import AmqpAbc


class RedisAmqpAbc(AmqpAbc, ABC):
    def __init__(
        self,
        redis: Redis,
        logger: logging.Logger = None,
        listening_periodicity: float = 0.01,
        timeout: int = 10,
        **kwargs,
    ):
        self.redis: Redis = redis
        self.logger = logger or logging
        self.timeout = timeout
        self.listening_periodicity = listening_periodicity
        self.queues_extra = {}

    async def consumer_callback(self, routing_key: str, on_message: callable):
        """
        Слушатель сообщений из очереди
        :param routing_key:             название очереди
        :param on_message:              callback получения сообщения
        """
        while True:
            message = await self.get_message(routing_key)
            self.logger.debug("Обработка сообщения из очереди %s...", routing_key)
            try:
                if asyncio.iscoroutinefunction(on_message):
                    await on_message(message)
                else:
                    await asyncio.to_thread(on_message, message)
                self.logger.debug("Обработка сообщения из очереди %s прошла успешно", routing_key)
            except:  # noqa
                self.logger.error("Ошибка при обработки сообщения из очереди %s", routing_key)
                self.logger.error(traceback.format_exc())


class MessageRedisAbc(ABC):
    def __init__(
        self,
        redis: Redis,
        routing_key: str,
        body: Any,
        noack: bool,
        rollback_on_error: bool,
        logger: logging.Logger,
        **kwargs,
    ):
        self.redis = redis
        self.routing_key = routing_key
        self.body = body
        self.noack = noack
        self.rollback_on_error = rollback_on_error
        self.logger = logger

    async def __aenter__(self):
        if not self.noack:
            await self.ack()
        await self.delete()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            if self.rollback_on_error:
                await self.rollback()

    @abstractmethod
    async def delete(self):
        pass

    @abstractmethod
    async def ack(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass
