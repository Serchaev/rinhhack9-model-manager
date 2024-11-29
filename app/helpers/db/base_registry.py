from abc import abstractmethod
from datetime import datetime
from typing import Any, Optional, Union
from uuid import uuid4

from sqlalchemy import delete, insert, select, table, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.helpers.db.connection import SessionManager
from app.helpers.exceptions import ObjectNotFound
from app.helpers.interfaces.registry_abc import RegistryABC


class BaseDbRegistry(RegistryABC):
    def __init__(self, session_manager: SessionManager, paranoid: bool = False, partitions: bool = False):
        """
        Базовый класс взаимодействия с моделями бд
        :param session_manager:         Менеджер сессий
        :param paranoid:                Режим удаления флагами(date_deleted)
        """
        self.transactional_session: async_sessionmaker = session_manager.transactional_session
        self.async_session_factory: async_sessionmaker = session_manager.async_session_factory
        self.paranoid = paranoid
        self.partitions = partitions

    @property
    @abstractmethod
    def model(self) -> table:
        """
        Модель sqlalchemy
        :return:    model
        """
        pass

    @property
    def primary_key(self) -> str:
        return "uuid"

    async def check_on_exist(self, uuid) -> None:
        """
        Проверка на существования объекта в бд
        :param uuid:        уникальный идентификатор объекта
        :return:            None или Error
        """
        obj = await self.get(uuid)
        if not obj:
            raise ObjectNotFound(f"Объекта с таким уникальным идентификатором:{uuid} не существует")

    async def get(self, uuid, default: Any = None) -> Optional[table]:
        """
        Получить объект по значению первичного ключа
        :param uuid:            значение первичного ключа
        :param default:         значение по умолчанию
        :return:                объект или значение по умолчанию
        """
        async with self.async_session_factory() as session:
            query = self._get_query().filter(getattr(self.model, self.primary_key) == uuid)
            obj = await session.execute(query)
            obj = obj.scalars().first()
        return obj or default

    async def find(
        self, filters: Any = None, sorts: Any = None, is_pagination: bool = False, **kwargs
    ) -> Union[list, select]:
        """
        Поиск объектов
        :param filters:          фильтры
        :param sorts:            сортировки
        :param is_pagination:    флаг пагинации
        :param kwargs:           дополнительные параметры
        :return:                 лист объектов
        """
        query = self._get_query()
        query = self._set_filter(query, filters)
        query = self._set_sort(query, sorts)
        return await self._get_response(query, is_pagination)

    async def paginate_find(self, filters: Any = None, sorts: Any = None, paginator: callable = None, **kwargs):
        query = await self.find(filters=filters, sorts=sorts, is_pagination=True)
        async with self.async_session_factory() as session:
            return await paginator(session, query, **kwargs)

    async def _get_response(self, query, is_pagination: bool):
        if is_pagination:
            return query
        async with self.async_session_factory() as session:
            result = await session.execute(query)
            return result.scalars().unique().all()

    async def create(self, **kwargs) -> str:
        """
        Создание объекта
        :param kwargs:      поля объекта
        :return:            str
        """
        if self.partitions:
            kwargs["uuid"] = kwargs.get("uuid") or str(uuid4())
            async with self.transactional_session() as session:
                query = insert(self.model).values(**kwargs)
                await session.execute(query)
                await session.commit()
            return kwargs["uuid"]
        model = self.model(**kwargs)
        async with self.transactional_session() as session:
            session.add(model)
            await session.commit()
        return str(model.uuid)

    async def bulk_create(self, *args) -> None:
        """
        Создание множества объекта
        :param args:        объекты
        :return:            None
        """
        objects = [self.model(**obj) for obj in args]
        async with self.transactional_session() as session:
            session.add_all(objects)
            await session.commit()

    async def update(self, uuid, **kwargs) -> None:
        """
        Обновление объекта
        :param uuid:          значение первичного ключа
        :param kwargs:        поля объекта
        :return:              None
        """
        if kwargs:
            await self.check_on_exist(uuid)
            async with self.transactional_session() as session:
                query = update(self.model).values(**kwargs).where(getattr(self.model, self.primary_key) == uuid)
                await session.execute(query)
                await session.commit()

    async def bulk_update(self, uuids: list, **kwargs) -> None:
        """
        Обновление множества объектов
        :param uuids:         уникальные идентификаторы объектов
        :param kwargs:        поля объекта
        :return:              None
        """
        if kwargs and uuids:
            async with self.transactional_session() as session:
                query = update(self.model).values(**kwargs).where(getattr(self.model, self.primary_key).in_(uuids))
                await session.execute(query)
                await session.commit()

    async def delete(self, uuid) -> None:
        """
        Удаление объекта
        :param uuid:          уникальный идентификатор объекта
        :return:              None
        """
        await self.check_on_exist(uuid)
        async with self.transactional_session() as session:
            if self.paranoid:
                query = (
                    update(self.model)
                    .values(date_deleted=datetime.now())
                    .filter(getattr(self.model, self.primary_key) == uuid)
                )
            else:
                query = delete(self.model).where(getattr(self.model, self.primary_key) == uuid)
            await session.execute(query)
            await session.commit()

    async def bulk_delete(self, uuids: list) -> None:
        """
        Удаление объектов
        :param uuids:         уникальные идентификаторы объектов
        :return:              None
        """
        if uuids:
            async with self.transactional_session() as session:
                if self.paranoid:
                    query = (
                        update(self.model)
                        .values(date_deleted=datetime.now())
                        .filter(getattr(self.model, self.primary_key).in_(uuids))
                    )
                else:
                    query = delete(self.model).filter(getattr(self.model, self.primary_key).in_(uuids))
                await session.execute(query)
                await session.commit()

    def _get_query(self):
        """
        Получить select
        :return:    select
        """
        query = select(self.model)
        if self.paranoid:
            query = query.filter(self.model.date_deleted.is_(None))
        return query

    @abstractmethod
    def _set_filter(self, query: select, filters: Any = None, **kwargs) -> select:
        """
        Задать фильтры для запроса
        :param query:       запрос
        :param filters:     фильтры
        :param kwargs:      дополнительные параметры
        :return:
        """
        pass

    @abstractmethod
    def _set_sort(self, query: select, sorts: Any = None, **kwargs) -> select:
        """
        Задать сортировки для запроса
        :param query:       запрос
        :param sorts:       сортировки
        :param kwargs:      дополнительные параметры
        :return:
        """
        pass
