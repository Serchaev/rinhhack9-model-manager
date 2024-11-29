from dataclasses import dataclass
from math import ceil
from typing import Any, NamedTuple, Optional, Union

from sqlalchemy import MappingResult, ScalarResult, func, select
from sqlalchemy.engine import FilterResult
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_scoped_session
from sqlalchemy.orm import noload

from app.helpers.interfaces.pagination_abc import PageParamsAbc


@dataclass
class RawParams:
    """Параметры для limit offset в бд"""

    limit: Optional[int] = None
    offset: Optional[int] = None
    include_total: bool = True

    def as_slice(self) -> slice:
        return slice(
            self.offset,
            (self.offset or 0) + self.limit if self.limit is not None else None,
        )


class RawPage(NamedTuple):  # оверхед NamedTuple куда меньше чем у dataclass
    """Страница"""

    items: list
    total: int
    page: int
    pages: int
    size: int

    @classmethod
    def create(cls, items: list, total: int, params: PageParamsAbc):
        return cls(
            items=items,
            total=total,
            page=params.page,
            pages=ceil(total / params.size),
            size=len(items),
        )

    def dict(self) -> dict:
        return self._asdict()


def count_query(query: select, *, use_subquery: bool = True) -> select:
    """
    Добавление к квери количества
    :param query:           квери
    :param use_subquery:    флаг выбора варианта добавления количества
    :return:                квери количества
    """
    query = query.order_by(None).options(noload("*"))

    if use_subquery:
        return select(func.count()).select_from(query.subquery())

    return query.with_only_columns(
        func.count(),
        **{"maintain_column_froms": True},
    )


def generic_query_apply_params(q: select, params: RawParams) -> select:
    """
    Добавление к квери limit и offset
    :param q:           квери
    :param params:      параметры
    :return:            квери
    """
    if params.limit is not None:
        q = q.limit(params.limit)
    if params.offset is not None:
        q = q.offset(params.offset)
    return q


def _maybe_unique(result: Any, unique: bool, response_type: FilterResult) -> Any:
    """
    Установка уникальности к результату
    :param result:           результат запроса sqlalchemy
    :param unique:           флаг уникальности
    :return:                 результат
    """
    result = result.unique() if unique else result
    if response_type == ScalarResult:
        result = ScalarResult(result, 1)
    elif response_type == MappingResult:
        result = MappingResult(result)
    else:
        raise NotImplementedError(f"Определите _maybe_unique для такого типа {response_type}")
    return result.all()


async def paginate(
    conn: Union[AsyncSession, AsyncConnection, async_scoped_session],
    query: select,
    params: Optional[PageParamsAbc] = None,
    subquery_count: bool = True,
    unique: bool = True,
    response_type: FilterResult = ScalarResult,
) -> RawPage:
    """
    Пагинация
    :param conn:                сессия алхимии
    :param query:               квери
    :param params:              параметры
    :param subquery_count:      флаг подсчёта количества через сабквери
    :param unique:              флаг уникальности
    :param response_type:       тип результата от sqlalchemy
    :return:                    результат
    """
    if params:
        raw_params: RawParams = params.get_raw_params()
    else:
        raw_params = RawParams()
    total = None
    if raw_params.include_total:
        total = await conn.scalar(count_query(query, use_subquery=subquery_count))

    query = generic_query_apply_params(query, raw_params)
    items = _maybe_unique(await conn.execute(query), unique, response_type)
    return RawPage.create(
        items=items,
        total=total,
        params=params,
    )
