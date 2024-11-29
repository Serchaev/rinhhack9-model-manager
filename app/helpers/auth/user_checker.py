from fastapi import HTTPException

from app.helpers.auth.schemas import User


def check_user(
    user: User,
    is_active: bool = True,
    is_verified: bool | None = None,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
):
    if is_active and not user.is_active:
        raise HTTPException(status_code=403, detail="Учетная запись не активна")
    if is_verified is not None and user.is_verified != is_verified:
        raise HTTPException(status_code=403, detail="Учетная запись не подтверждена")
    if roles is not None:
        user_roles = [role.name for role in user.roles]
        if not any(role in user_roles for role in roles):
            raise HTTPException(status_code=403, detail="Отсутствуют необходимые роли")
    if permissions is not None:
        all_permissions_names = set(
            [permission.name for role in user.roles for permission in role.permissions]
            + [permission.name for permission in user.permissions]
        )
        if not any(permission in all_permissions_names for permission in permissions):
            raise HTTPException(status_code=403, detail="Отсутствуют необходимые права")
