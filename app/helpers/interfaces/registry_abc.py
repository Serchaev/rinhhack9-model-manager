from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID


class RegistryABC(ABC):
    @abstractmethod
    async def create(self, **kwargs) -> str:
        """
        Создание объекта
        :param kwargs:      поля объекта
        :return:            уникальный идентификатор
        """
        pass

    @abstractmethod
    async def bulk_create(self, *args) -> None:
        """
        Создание множества объекта
        :param args:        объекты
        :return:            None
        """
        pass

    @abstractmethod
    async def update(self, uuid: UUID, **kwargs) -> None:
        """
        Обновление объекта
        :param uuid:          уникальный идентификатор объекта
        :param kwargs:        поля объекта
        :return:              None
        """
        pass

    @abstractmethod
    async def bulk_update(self, uuids: list[UUID], **kwargs) -> None:
        """
        Обновление множества объекта
        :param uuids:         уникальные идентификаторы объектов
        :param kwargs:        поля объекта
        :return:              None
        """
        pass

    @abstractmethod
    async def delete(self, uuid: UUID) -> None:
        """
        Удаление объекта
        :param uuid:          уникальный идентификатор объекта
        :return:              None
        """
        pass

    @abstractmethod
    async def bulk_delete(self, uuids: list[UUID]) -> None:
        """
        Удаление объектов
        :param uuids:         уникальные идентификаторы объектов
        :return:              None
        """
        pass

    @abstractmethod
    async def find(
        self,
        filters: Any = None,
        sorts: Any = None,
        is_pagination: bool = False,
    ) -> Optional[list]:
        """
        Поиск объектов
        :param filters:          фильтры
        :param sorts:            сортировка
        :param is_pagination:    флаг пагинации
        :return:                 лист объектов
        """
        pass

    @abstractmethod
    async def paginate_find(self, filters: Any = None, sorts: Any = None, paginator: callable = None, **kwargs):
        """
        Поиск объектов
        :param filters:          фильтры
        :param sorts:            сортировка
        :param paginator:        функция пагинирования
        :param kwargs:           дополнительные параметры
        :return:                 лист объектов
        """
        pass
