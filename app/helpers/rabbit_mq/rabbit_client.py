import asyncio
import json
import logging
from typing import Any, Union

from aio_pika import Message, connect_robust
from yarl import URL

from app.helpers.interfaces import AmqpAbc


class RabbitClient(AmqpAbc):
    def __init__(
        self,
        host: str,
        port: Union[str, int],
        login: str,
        password: str,
        protocol: str = "amqp",
        timeout: int = 10,
        logger: logging.Logger = None,
    ):
        """
        :param protocol:            протокол
        :param host:                хост
        :param port:                порт
        :param login:               логин
        :param password:            пароль
        :param logger:              логгер
        :param loop:                AbstractEventLoop
        """
        self.connection = None
        self.queues = {}
        self.channel = None

        self.logger = logger or logging
        self.protocol = protocol
        self.host = host
        self.port = port
        self.login = login
        self.password = password
        self.timeout = timeout

    @property
    def url(self) -> URL:
        return URL(f"{self.protocol}://{self.login}:{self.password}@{self.host}:{self.port}/")

    async def connect(self, **kwargs) -> None:
        """
        Подключение к rabbit
        :param kwargs:      дополнительные параметры подключения
        :return:
        """
        self.connection = await connect_robust(url=self.url, loop=self.loop, **kwargs)
        self.channel = await self.connection.channel()
        self.logger.info("Подключение к rabbitmq %s прошло успешно", self.url.with_password("******"))

    async def init_queue(self, routing_key: str, **kwargs) -> None:
        """
        Инициализация очереди.
        :param routing_key:     название очереди
        :param kwargs:          дополнительные параметры
        :return:
        """
        if self.connection and self.channel:
            self.queues[routing_key] = await self.channel.declare_queue(name=routing_key, **kwargs)
            self.logger.info("Создана очередь %s", routing_key)
        else:
            raise ConnectionError("Отсутствует подключение rabbitmq или не создан канал")

    async def close(self) -> None:
        """
        Закрытие подключения
        :return:
        """
        if not self.connection.is_closed:
            await self.connection.close()
        self.logger.info("Закрытие подключения к rabbitmq %s прошло успешно", self.url.with_password("******"))

    async def init_consumer(self, routing_key: str, on_message: callable, **kwargs) -> None:
        """
        Инициализация слушателя
        :param routing_key:     название очереди
        :param on_message:      каллбек для слушателя
        :param kwargs:          дополнительные параметры
        :return:
        """
        await self.queues[routing_key].consume(callback=on_message, **kwargs)

    async def send(self, message: Union[str, bytes, dict, list], routing_key: str, **kwargs) -> None:
        """
        Отправка сообщения
        :param message:         сообщение
        :param routing_key:     название очереди
        :param kwargs:          дополнительные параметры
        :return:
        """
        if isinstance(message, str):
            message = message.encode("utf-8")
        elif isinstance(message, (dict, list)):
            message = json.dumps(message).encode("utf-8")
        elif isinstance(message, bytes):
            message = message
        else:
            raise TypeError(f"Не поддерживаемы тип сообщения {type(message)}")

        aio_pika_message = Message(
            body=message, headers=kwargs.get("headers", {}), delivery_mode=kwargs.get("delivery_mode")
        )
        asyncio.create_task(self.channel.default_exchange.publish(aio_pika_message, routing_key=routing_key))
        self.logger.info("Отправка сообщения в очередь %s прошло успешно", routing_key)

    async def get_message(self, routing_key: str) -> Any:
        while True:
            message = await self.queues[routing_key].get(timeout=self.timeout, fail=False)
            if message:
                await message.ack()
                return message
            await asyncio.sleep(0.01)
