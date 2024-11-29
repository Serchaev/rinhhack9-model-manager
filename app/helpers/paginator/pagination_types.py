from typing import Generic, Optional, Sequence, TypeVar

from fastapi import HTTPException, Query
from pydantic import BaseModel

from app.helpers.paginator.pagination import PageParamsAbc, RawParams

T = TypeVar("T")


class PageParams(BaseModel, PageParamsAbc):
    page: int = Query(1, description="Page size limit")
    size: int = Query(50, description="Page offset")

    def get_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=(self.page - 1) * self.size,
        )

    @classmethod
    def query_parameters(
        cls,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(50, ge=1, le=100, description="Page size"),
    ) -> "PageParams":
        if page <= 0 or size < 0:
            raise HTTPException(status_code=400, detail="Неверные параметры пагинации")
        return cls(page=page, size=size)


class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    page: Optional[int]
    size: Optional[int]
    total: Optional[int]
    pages: Optional[int] = None

    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True,
    }
