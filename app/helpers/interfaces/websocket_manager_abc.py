from abc import ABC, abstractmethod
from typing import Any, Optional, Union


class WebsocketManagerAbc(ABC):
    @abstractmethod
    async def connect(self, websocket: Any, connection_id: Optional[str] = None) -> str:
        """
        Подключение websocket
        :param websocket:               websocket
        :param connection_id:           ID подключения
        :return: None
        """
        pass

    @abstractmethod
    async def disconnect(self, connection_id: str) -> bool:
        """
        Отключение websocket
        :param connection_id:           ID подключения
        :return: None
        """
        pass

    @abstractmethod
    async def send(self, message: Union[str, dict, list, bytes], connection_id: str) -> None:
        """
        Отправка сообщения в websocket
        :param message:                 Сообщение
        :param connection_id:           ID подключения
        :return: None
        """
        pass

    @abstractmethod
    async def receive(self, connection_id: str, timeout: Optional[float] = None) -> str:
        """
        Получение сообщения из websocket
        :param connection_id:           ID подключения
        :param timeout:                 Время ожидания сообщения
        :return: None
        """
        pass

    @abstractmethod
    async def broadcast(self, message: Union[str, dict, list, bytes]) -> None:
        """
        Отправка сообщения всем websocket
        :param message:           сообщение
        :return: None
        """
        pass

    async def ping(self, connection_id: str) -> bool:
        """
        Пинг
        :param connection_id:           ID подключения
        :return: bool
        """
        pass

    @abstractmethod
    async def websocket_handler(self, connection_id: str, func: callable, repeat_timeout: float = 1):
        """
        Обработчик для вебсокета
        :param connection_id:           ID подключения
        :param func:                    функция каллбека
        :param repeat_timeout:          таймаут повторений
        :return: None
        """
        pass
