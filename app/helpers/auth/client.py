import warnings

import aiohttp
from fastapi import HTTPException

from app.helpers.aiohttp_client import AioHttpClient
from app.helpers.auth.schemas import User
from app.helpers.auth.token_provider import AuthTokenProvider
from app.helpers.interfaces.auth_abc import AuthClient
from app.helpers.redis import RedisCache


class AuthAiohttpClient(AioHttpClient, AuthClient):
    def __init__(
        self,
        cache_wrapper: RedisCache.cache = None,
        current_user_endpoint: str = "/users/me",
        get_user_ttl: int = 60,
        roles_endpoint: str = "/roles",
        token_endpoint: str = "/auth/jwt/login",
        authenticate_ttl: int = 60,
        service_login: str = None,
        service_password: str = None,
        token_provider: AuthTokenProvider = None,  # TODO: обязательно передавать token_provider
        *args,
        **kwargs,
    ):
        """
        Клиент для работы с сервисом авторизации
        :param cache_wrapper(ttl=60, timeout=0.07): декоратор кэша с такими аргументами
        :param current_user_endpoint: эндпоинт для получения текущего пользователя
        :param get_user_ttl: время жизни кэша для получения текущего пользователя
        :param roles_endpoint: эндпоинт для получения ролей
        :param args: для aiohttp.ClientSession
        :param kwargs: для aiohttp.ClientSession
        """

        if not token_provider:
            warnings.warn("Необходимо передавать инициализированный AuthTokenProvider")

        if token_endpoint or authenticate_ttl or service_login or service_password:
            # TODO: убрать данные параметры из AuthAiohttpClient
            warnings.warn(
                "Использование параметров token_endpoint, authenticate_ttl, service_login, service_password "
                "устарело для AuthAiohttpClient"
            )

        self.cache_wrapper = cache_wrapper
        if current_user_endpoint[0] != "/":
            # Для обратной совместимости, когда не указывали вначале слеш
            current_user_endpoint = f"/{current_user_endpoint}"
        self.current_user_endpoint = current_user_endpoint
        self.get_user_ttl = get_user_ttl
        self.roles_endpoint = roles_endpoint

        if self.cache_wrapper:
            self.get_user = self.cache_wrapper(ttl=self.get_user_ttl)(self.get_user)

        self.token_provider = token_provider or AuthTokenProvider(  # TODO: убрать инициализацию после мажорной версии
            protocol=kwargs.get("protocol", "http"),
            host=kwargs.get("host", "localhost"),
            port=kwargs.get("port", 5555),
            endpoint=token_endpoint,
            service_login=service_login,
            service_password=service_password,
            cache_wrapper=cache_wrapper,
            authenticate_ttl=authenticate_ttl,
        )

        super().__init__(*args, **kwargs)

    async def get_all(self, url, token=None, size=100, order_by="uuid", model=None):
        """
        Получение всех объектов из пагинации
        :param url: эндпоинт (например `/users`)
        :param token: токен
        :param size: размер получение пачки за раз
        :param order_by: сортировка
        :param model: пидантик модель опционально
        """
        page = 1
        params = {"order_by": order_by, "page": page, "size": size}

        items_list = []
        has_more_pages = True

        while has_more_pages:
            items = await self.get(url=url, token=token, params=params)

            if model:
                items_list.extend([model(**item) for item in items["items"]])
            else:
                items_list.extend(items["items"])

            has_more_pages = page < items["pages"]
            if has_more_pages:
                page += 1
                params["page"] = page

        return items_list

    async def get_user(self, token: str) -> dict:
        # TODO: возвращать объект User. При изменении потеряется обратная совместимость.
        return await self.get(f"{self.current_user_endpoint}", token)

    async def _get_response_detail(self, response) -> str:
        # TODO: оставлено на всякий для обратной совместимости
        return await self.token_provider._get_response_detail(response)

    async def get(self, url, token=None, params=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    resp = await response.json()
                    return resp
                detail = await self._get_response_detail(response)
                raise HTTPException(status_code=response.status, detail=detail)
        except aiohttp.ClientError as e:
            status = getattr(e, "status", None)
            if status:
                raise HTTPException(status_code=status, detail=e.message)
            raise HTTPException(500, "Сервис авторизации недоступен")

    async def service_token(self):
        # TODO: оставлено для обратной совместимости
        return await self.token_provider.service_token()

    async def get_users_by_role(self, role_uuid: str):
        token = await self.service_token()
        url = f"{self.roles_endpoint}/{role_uuid}"
        role = await self.get(url, token)
        users = [User(**u) for u in role.get("users", [])]
        return users
