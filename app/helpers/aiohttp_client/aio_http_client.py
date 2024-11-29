import warnings
from typing import Union

from aiohttp import ClientSession, ClientTimeout


class AioHttpClient:
    def __init__(
        self,
        protocol: str,
        host: str,
        port: Union[int, str],
        endpoint: str = None,
        raise_for_status: bool = True,
        timeout: int = 30,
        extra: dict = None,
        **kwargs,
    ):
        """
        Клиент для подключения к http сервисам
        :param protocol:                протокол
        :param host:                    хост
        :param port:                    порт
        :param endpoint:                точка доступа
        :param raise_for_status:        raise ошибки при статусах-ошибках
        :param timeout:                 таймаут в секундах
        :param loop:                    loop
        :param extra:                   дополнительные параметры сессии
        :param kwargs:                  дополнительные параметры
        """
        self.session = None

        self.protocol = protocol
        self.host = host
        self.port = port
        if endpoint:
            warnings.warn("Использование параметра endpoint устарело для AioHttpClient.")
        self.endpoint = endpoint
        self.extra = extra or {}
        self.timeout = timeout
        self.raise_for_status = raise_for_status

    async def init_session(self) -> None:
        self.session = await self.create_session()

    async def close_session(self) -> None:
        if self.session:
            await self.session.close()

    async def create_session(self) -> ClientSession:
        """
        ClientSession необходимо создавать в async функции
        """
        return ClientSession(
            base_url=self.url,
            raise_for_status=self.raise_for_status,
            timeout=ClientTimeout(total=self.timeout),
            **self.extra,
        )

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"
