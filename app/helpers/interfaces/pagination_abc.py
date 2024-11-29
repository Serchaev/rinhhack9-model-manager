from abc import ABC, abstractmethod


class PaginationParamsABC(ABC):
    @abstractmethod
    def get_raw_params(self):
        pass

    @classmethod
    @abstractmethod
    def query_parameters(cls) -> dict:
        pass


class PageParamsAbc(PaginationParamsABC, ABC):
    page: int
    size: int
