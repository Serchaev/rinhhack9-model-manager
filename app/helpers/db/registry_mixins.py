from typing import Any

from sqlalchemy import select


class FastApiFilterMixin:
    def _set_filter(self, query: select, filters: Any = None, **kwargs) -> select:
        if filters:
            query = filters.filter(query)
        return query


class FastApiSortMixin:
    def _set_sort(self, query: select, sorts: Any = None, **kwargs) -> select:
        if sorts:
            query = sorts.sort(query)
        return query
