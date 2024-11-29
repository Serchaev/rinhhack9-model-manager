from fastapi import Depends, HTTPException, Request

from app.helpers.auth.keycloak_auth_middlware import KeycloakMiddleware
from app.helpers.auth.schemas import Role, User
from app.helpers.interfaces.auth_abc import AuthClient


class AuthMixinDependencies:
    """
    Класс для добавления в роут авторизации
    :attr auth_enabled:            флаг работы проверки
    :attr current_user:            функция проверки пользователя
    :attr cache_ttl:               время жизни кэша в секундах
    :attr auth_client:             клиент для работы с сервисом авторизации
    :attr security:                секьюрити для получения токена
    """

    auth_enabled: bool = True
    auth_client: callable = None
    security: callable = None

    @classmethod
    def _set_auth(cls):
        if not (cls.auth_client and cls.security):
            raise NotImplementedError("Необходимо указать aiohttp_client, security")

        async def get_user(
            auth_client: AuthClient = Depends(cls.auth_client), token: str = Depends(cls.security)
        ) -> User:
            return await cls._get_user(auth_client, token)

        def set_user(request: Request, user: User = Depends(get_user)):
            return cls._user_setter(request, user)

        return set_user if cls.auth_enabled else lambda: None

    @staticmethod
    async def _get_user(auth_client: AuthClient, token: str) -> User:
        user = await auth_client.get_user(token)
        return User(**user)

    @staticmethod
    def _user_setter(request: Request, user: User):
        if isinstance(user, dict):
            user = User(**user)
        request.scope["user"] = user


class KeycloakAuthDependencies:
    """
    Класс для добавления авторизации через Keycloak
    :attr auth_enabled:            флаг работы проверки
    :attr middleware:              миддлварь
    """

    auth_enabled: bool = True
    middleware: KeycloakMiddleware = None

    @classmethod
    def _set_auth(cls) -> callable:
        if not cls.middleware:
            raise NotImplementedError("Необходимо указать middleware")

        async def _get_user(request: Request) -> User:
            return await cls.get_user(request)

        def set_user(request: Request, user: User = Depends(_get_user)) -> None:
            return cls._user_setter(request, user)

        return set_user if cls.auth_enabled else lambda: None

    @staticmethod
    async def get_user(request: Request) -> User:
        user_info = request.scope.get("user_info")
        user_roles = request.scope.get("user_roles")
        if not user_info or not user_roles:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return User(
            uuid=user_info.get("sub"),
            login=user_info.get("preferred_username"),
            email=user_info.get("email"),
            surname=user_info.get("family_name"),
            name=user_info.get("given_name"),
            patronymic=user_info.get("patronymic"),
            jdata=user_info.get("jdata", {}),
            is_active=True,
            is_verified=user_info.get("email_verified", False),
            roles=[Role(name=role) for role in user_roles],
            permissions=user_info.get("permissions", []),
        )

    @staticmethod
    def _user_setter(request: Request, user: User) -> None:
        request.scope["user"] = user
