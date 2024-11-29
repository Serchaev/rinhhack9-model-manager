from abc import ABC, abstractmethod
from json import dumps
from typing import Any, Union


class AmqpAbc(ABC):
    """
    Абстрактный класс для реализации amqp
    """

    @staticmethod
    def convert_message(message: Union[str, bytes, list, dict]) -> bytes:
        """
        Конвертация сообщения в bytes
        :param message:     сообщение
        :return:            сообщение в bytes
        """
        if isinstance(message, str):
            return message.encode("utf-8")
        if isinstance(message, (list, dict)):
            return dumps(message).encode("utf-8")
        return message

    @abstractmethod
    async def init_queue(self, routing_key: str, **kwargs) -> None:
        """
        Инициализация очереди
        :param routing_key:         название очереди
        :param kwargs:              дополнительные параметры
        :return:                    None
        """
        pass

    @abstractmethod
    async def send(self, message: Union[str, bytes, list, dict], routing_key: str, **kwargs) -> None:
        """
        Отправка сообщения в очередь
        :param message:             сообщение
        :param routing_key:         название очереди
        :return:                    None
        """
        pass

    @abstractmethod
    async def init_consumer(self, routing_key: str, on_message: callable, **kwargs) -> None:
        """
        Инициализация слушателя очереди
        :param routing_key:             название очереди
        :param on_message:              callback получения сообщения
        :return:                        None
        """
        pass

    @abstractmethod
    async def get_message(self, routing_key: str) -> Any:
        """
        Получить сообщение из очереди
        :param routing_key:             название очереди
        :return:                        Any
        """

    # TODO: разработать для всех клиентов метод получения пачки сообщений
    # @abstractmethod
    # async def get_messages(self, routing_key: str) -> Any:
    #     """
    #     Получить сообщение из очереди
    #     :param routing_key:             название очереди
    #     :return:                        Any
    #     """
