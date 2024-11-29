import logging
from abc import ABC, abstractmethod


class MiddlewareAbc(ABC):
    def __init__(self, middleware_class, logger: logging.Logger):
        """
        :param: middleware_class тип middleware
        :param: logger           логгер
        """
        self.middleware_class = middleware_class
        self.logger = logger or logging

    @abstractmethod
    async def __call__(self, request, call_next):
        pass
