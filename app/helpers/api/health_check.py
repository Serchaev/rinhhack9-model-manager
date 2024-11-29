from typing import Optional

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    version: str = Field(description="Версия сервиса")
    commit: Optional[str] = Field(description="Коммит")
    branch: Optional[str] = Field(description="Ветка")
    status: bool = Field(description="Статус сервиса")
    service: str = Field(description="Название сервиса")


def add_health_check_router(
    app: FastAPI,
    service: str,
    version: str,
    branch: str,
    commit: str,
):
    """
    Добавление запроса здоровья GET /healthcheck/
    :param app:         объект fast_api
    :param service:     название сервиса
    :param version:     версия
    :param branch:      ветка
    :param commit:      коммит
    """
    health_check_router = APIRouter(prefix="/healthcheck", tags=["Healthcheck"])

    @health_check_router.get("/")
    def get_health_check() -> HealthCheck:
        """
        Запрос здоровья
        """
        return HealthCheck(
            version=version,
            service=service,
            branch=branch,
            commit=commit,
            status=True,
        )

    app.include_router(health_check_router)
