from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, model_validator
from pydantic.fields import Field


class Permission(BaseModel):
    """
    Доступ
    """

    uuid: UUID = Field(description="Уникальный идентификатор")
    name: str = Field(description="Название")
    jdata: Optional[dict] = Field(description="Дополнительные данные")


class Role(BaseModel):
    """
    Роль
    """

    uuid: Optional[UUID] = Field(default=None, description="Уникальный идентификатор")
    name: str = Field(description="Название")
    jdata: Optional[dict] = Field(default_factory=dict, description="Дополнительные данные")
    permissions: Optional[list[Permission]] = Field(description="Доступы", default_factory=list)


class User(BaseModel):
    """
    Пользователь
    """

    uuid: UUID = Field(description="Уникальный идентификатор")

    login: str = Field(description="Логин пользователя")
    email: Optional[EmailStr] = Field(description="Почта")

    surname: Optional[str] = Field(description="Фамилия")
    name: Optional[str] = Field(description="Имя")
    patronymic: Optional[str] = Field(description="Отчество")

    jdata: Optional[dict] = Field(description="Дополнительные данные")
    is_active: bool = Field(description="Флаг активности")
    is_verified: bool = Field(description="Флаг верификации пользователя")
    roles: Optional[list[Role]] = Field(description="Роли", default_factory=list)
    permissions: Optional[list[Permission]] = Field(description="Доступы", default_factory=list)

    @model_validator(mode="before")
    def check_id_or_uuid(cls, values):
        if "id" in values:
            values["uuid"] = values.pop("id")
        elif "uuid" not in values:
            raise ValueError("Either id or uuid must be provided.")
        return values

    def __hash__(self):
        return hash(self.uuid)

    def __eq__(self, other):
        if isinstance(other, User):
            return self.uuid == other.uuid
        return False
