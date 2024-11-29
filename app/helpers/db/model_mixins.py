from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr


class UuidModelMixin:
    __abstract__ = True

    uuid = Column(
        UUID,
        primary_key=True,
        index=True,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
        unique=True,
        doc="Уникальный идентификатор объекта",
        comment="Уникальный идентификатор объекта",
    )


class TimeStampModelMixin:
    __abstract__ = True
    _date_created_index = False
    _date_created_primary_key = False
    _date_updated_index = False

    @declared_attr
    def date_created(self):
        return Column(
            DateTime(timezone=True),
            nullable=False,
            primary_key=self._date_created_primary_key,
            index=self._date_created_index if not self._date_created_primary_key else True,
            server_default=func.now(),
            doc="Дата создания",
            comment="Дата создания",
        )

    @declared_attr
    def date_updated(self):
        return Column(
            DateTime(timezone=True),
            nullable=False,
            index=self._date_updated_index,
            server_default=func.now(),
            onupdate=lambda: datetime.now(timezone.utc).astimezone(),  # TODO: перенос на триггер
            doc="Дата редактирования",
            comment="Дата редактирования",
        )


class DateDeletedModelMixin:
    __abstract__ = True
    _date_deleted_index = False

    @declared_attr
    def date_deleted(self):
        return Column(
            DateTime(timezone=True),
            index=self._date_deleted_index,
            nullable=True,
            default=None,
            doc="Дата удаления",
            comment="Дата удаления",
        )
