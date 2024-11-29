import logging
from time import time
from traceback import format_exc

from fastapi import Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

from app.helpers.interfaces.middleware import MiddlewareAbc


class MetricsMiddleware(MiddlewareAbc):
    """
    Класс сбора метрик для prometheus
    """

    def __init__(self, middleware_class: type[BaseHTTPMiddleware], logger: logging.Logger = None):
        self.request_latency_seconds = Histogram(
            name="request_latency_seconds",
            documentation="Гистограмма времени выполнения запросов",
            labelnames=["path", "method"],
        )
        self.request_completed_total = Counter(
            name="request_completed_total",
            documentation="Счётчик выполненных запросов",
            labelnames=["path", "method"],
        )
        self.request_exceptions_total = Counter(
            name="request_exceptions_total",
            documentation="Счётчик выполненных с ошибками запросов",
            labelnames=["path", "method"],
        )
        super().__init__(middleware_class, logger)

    async def __call__(self, request: Request, call_next):
        start = time()
        try:
            response = await call_next(request)
        except Exception as error:  # noqa
            path = self.delete_path_params(request.scope["path"], request.path_params)
            self.logger.error(format_exc(chain=False))
            self.request_exceptions_total.labels(path=path, method=request.method).inc()
            return PlainTextResponse(status_code=500, content="Internal Server Error")
        path = self.delete_path_params(request.scope["path"], request.path_params)
        self.request_latency_seconds.labels(path=path, method=request.method).observe(time() - start)
        self.request_completed_total.labels(path=path, method=request.method).inc()
        return response

    @classmethod
    def delete_path_params(cls, path: str, path_params: dict) -> str:
        for path_param in path_params.values():
            path = path.replace(str(path_param), "")
        return path
