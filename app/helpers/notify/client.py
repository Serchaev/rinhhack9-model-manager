import logging

from app.helpers.aiohttp_client import AioHttpClient
from app.helpers.auth.token_provider import AuthTokenProvider


class NotifyClient(AioHttpClient):
    def __init__(
        self,
        token_provider: AuthTokenProvider,
        enabled: bool = True,
        logger: logging.Logger = None,
        *args,
        **kwargs,
    ):
        """
        Клиент для работы с сервисом уведомлений
        :param token_provider: провайдер токена
        :param enabled: вкл/выкл отправку уведомлений
        """
        self.token_provider = token_provider
        self.enabled = enabled
        self.logger = logger or logging
        super().__init__(*args, **kwargs)

    async def send(
        self,
        message: str,
        to_user: list[str] = None,
        to_role: list[str] = None,
        priority_uuid: str = None,
        surfacing: bool = True,
        endpoint: str = "notifications",
    ):
        """
        Отправка уведомления
        :param message: сообщение
        :param to_user: список юидников пользователей кому отправляем
        :param to_role: список юидников ролей кому отправляем
        :param priority_uuid: юид объекта содержащего информацию о приоритете
        :param surfacing: флаг определяет необходимость всплытия уведомления
        :param endpoint: путь запроса
        """
        if not self.enabled:
            try:
                service_token = await self.token_provider.service_token()
                data = {
                    "data": {
                        "message": message,
                        "to_user": to_user or [],
                        "to_role": to_role or [],
                    },
                    "priority_uuid": priority_uuid,
                    "surfacing": surfacing,
                }
                headers = {"Authorization": f"Bearer {service_token}"}
                async with self.session.post(f"/{endpoint}", json=data, headers=headers) as resp:
                    return await resp.json()
            except Exception as e:
                # для того чтобы не падал сервис при ошибке отправки уведомления
                self.logger.error(f"Ошибка при отправке уведомления {message!r}: {e}")
