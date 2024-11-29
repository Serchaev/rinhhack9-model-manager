from app.helpers.aiohttp_client import AioHttpClient
from app.helpers.redis import RedisCache


class AuthTokenProvider(AioHttpClient):
    def __init__(
        self,
        service_login: str = None,
        service_password: str = None,
        cache_wrapper: RedisCache.cache = None,
        authenticate_ttl: int = 60,
        *args,
        **kwargs,
    ):
        """
        Клиент для получения токена
        :param service_login: сервисный логин
        :param service_password: сервисный пароль
        :param cache_wrapper: декоратор кэша
        :param authenticate_ttl: время жизни кэша токена для сервиса
        :param args: для aiohttp.ClientSession
        :param kwargs: для aiohttp.ClientSession
        """
        self.cache_wrapper = cache_wrapper
        self.service_login = service_login
        self.service_password = service_password
        self.authenticate_ttl = authenticate_ttl

        if self.cache_wrapper:
            self.authenticate = self.cache_wrapper(ttl=self.authenticate_ttl)(self.authenticate)

        kwargs.update({"raise_for_status": False})
        super().__init__(*args, **kwargs)

    async def _get_response_detail(self, response) -> str:
        if response.content_type == "application/json":
            resp = await response.json()
            return resp.get("detail", "Неизвестная ошибка")
        return await response.text()

    async def authenticate(self, login, password, endpoint: str = "auth/jwt/login"):
        data = {"username": login, "password": password}
        async with self.session.post(url=f"/{endpoint}", data=data) as response:
            if response.status == 200:
                resp = await response.json()
                return resp.get("access_token")
            detail = await self._get_response_detail(response)
            # не HTTP эксепшены т.к. это внутренний метод у сервиса
            raise Exception(f"Не удалось аутентифицироваться: {detail}")
        raise Exception("Не указан логин и пароль")

    async def service_token(self):
        return await self.authenticate(self.service_login, self.service_password)
