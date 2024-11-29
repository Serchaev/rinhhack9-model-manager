from fastapi import Request

from app.helpers.auth.schemas import User
from app.helpers.auth.user_checker import check_user


def authorize(
    auth_enabled: bool = True,
    is_active: bool = True,
    is_verified: bool | None = None,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
):
    """
    Декоратор для методов (_find, _retrieve, _create, ...) миксинов из api.routers_mixin
    """

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            if auth_enabled:
                user: User = request.user
                check_user(
                    user=user,
                    is_active=is_active,
                    is_verified=is_verified,
                    roles=roles,
                    permissions=permissions,
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
