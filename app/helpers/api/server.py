import asyncio
import logging
import logging.config
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from setproctitle import setproctitle

from app.helpers.interfaces.middleware import MiddlewareAbc


class Server:
    """
    Класс для создания приложения сервиса
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: Optional[str] = "FastAPI Server",
        logging_config: Optional[dict] = None,
        cors_config: Optional[dict] = None,
        routers: list[APIRouter] = None,
        start_callbacks: list[callable] = None,
        stop_callbacks: list[callable] = None,
        exception_handlers: list[callable] = None,
        extensions: list[callable] = None,
        middlewares: list[MiddlewareAbc] = None,
        fast_api_extra: Optional[dict] = None,
    ) -> None:
        setproctitle(f"{name}::main")

        self.name = name
        self.version = version
        self.description = description

        self.logging_config = logging_config
        self.cors_config = cors_config

        self.routers = routers or []
        self.start_callbacks = start_callbacks or []
        self.stop_callbacks = stop_callbacks or []
        self.exception_handlers = exception_handlers or []
        self.extensions = extensions or []
        self.middlewares = middlewares or []
        self.fast_api_extra = fast_api_extra or {}
        self.app = FastAPI(
            title=name,
            version=version,
            description=description,
            lifespan=self._lifespan,
            **self.fast_api_extra,
        )
        if self.logging_config:
            self._init_logger()
        if self.cors_config:
            self._init_cors()
        self._init_routers()
        self._init_extensions()
        self._init_exception_handler()
        self._init_middlewares()

    def _init_extensions(self):
        for extension in self.extensions:
            extension(self.app)
        logging.info("Инициализация extensions прошла успешно")

    def _init_exception_handler(self):
        for handler in self.exception_handlers:
            handler(self.app)
        logging.info("Инициализация exception_handlers прошла успешно")

    def _init_routers(self):
        for router in self.routers:
            self.app.include_router(router)
        logging.info("Инициализация routers прошла успешно")

    def _init_middlewares(self):
        for middleware in self.middlewares:
            self.app.add_middleware(middleware.middleware_class, dispatch=middleware)
        logging.info("Инициализация middlewares прошла успешно")

    def _init_logger(self) -> None:
        logging.config.dictConfig(self.logging_config)
        logging.info("Инициализация logger прошла успешно")

    def _init_cors(self) -> None:
        self.app.add_middleware(CORSMiddleware, **self.cors_config)
        logging.info("Инициализация cors прошла успешно")

    @asynccontextmanager
    async def _lifespan(self, _app: FastAPI):
        for callback in self.start_callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                await asyncio.to_thread(callback)
        logging.info("Инициализация startup callbacks прошла успешно")

        yield

        for callback in self.stop_callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                await asyncio.to_thread(callback)
        logging.info("Инициализация shutdown callbacks прошла успешно")
