from abc import ABC
from typing import AsyncGenerator, Optional


class ClientHttpAbc(ABC):
    @classmethod
    def convert_filters(cls, filters: Optional[dict] = None) -> Optional[dict]:
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    filters[key] = ",".join(value)
        return filters or {}

    @classmethod
    async def get_object(cls, uuid: str, session, endpoint: str) -> dict:
        """
        Получить табличные данные объекта
        :param uuid:        уникальный идентификатор объекта
        :param session:     сессия
        :param endpoint:    путь запроса
        :return:            данные файла
        """
        async with session.get(f"/{endpoint}/{uuid}") as response:
            result = await response.json()
            return result

    @classmethod
    async def get_objects(cls, session, endpoint: str, filters: Optional[dict] = None) -> list[dict]:
        """
        Получить табличные данный объектов
        :param session:     сессия
        :param filters:     фильтры запроса
        :param endpoint:    путь запроса
        :return:            данные объектов
        """
        page = 1
        max_page = 1
        filters = cls.convert_filters(filters)
        result = []
        while page <= max_page:
            filters["page"] = page
            async with session.get(f"/{endpoint}/", params=filters) as response:
                response = await response.json()
                result.extend(response["items"])
                max_page = response["pages"]
            page += 1
        return result

    @classmethod
    async def get_objects_generator(cls, session, endpoint: str, filters: Optional[dict] = None) -> AsyncGenerator:
        """
        Получить табличные данный объектов
        :param session:     сессия
        :param filters:     фильтры запроса
        :param endpoint:    путь запроса
        :return:            генератор данных объектов
        """
        page = 1
        max_page = 1
        filters = cls.convert_filters(filters)
        while page <= max_page:
            filters["page"] = page
            async with session.get(f"/{endpoint}/", params=filters) as response:
                response = await response.json()
                yield response["items"]
                max_page = response["pages"]
            page += 1

    @classmethod
    async def delete_object(
        cls,
        uuid: str,
        session,
        endpoint: str,
    ) -> bool:
        """
        Удалить объект
        :param uuid:        уникальный идентификатор объекта
        :param session:     сессия
        :param endpoint:    путь запроса
        :return:            статус
        """
        async with session.delete(f"/{endpoint}/{uuid}") as response:
            result = await response.json()
            return result["status"]

    @classmethod
    async def update_object(
        cls,
        uuid,
        data: dict,
        session,
        endpoint: str,
    ) -> bool:
        """
        Обновить объект
        :param uuid:        уникальный идентификатор объекта
        :param session:     сессия
        :param data:        данные объекта
        :param endpoint:    путь запроса
        :return:            статус
        """
        async with session.put(f"/{endpoint}/{uuid}", json=data) as response:
            result = await response.json()
            return result["status"]

    @classmethod
    async def create_object(
        cls,
        data: dict,
        session,
        endpoint: str,
    ) -> str:
        """
        Создать объект
        :param session:     сессия
        :param data:        данные объекта
        :param endpoint:    путь запроса
        :return:            уникальный идентификатор созданного объекта
        """
        async with session.post(f"/{endpoint}/", json=data) as response:
            result = await response.json()
            return result["uuid"]
