import warnings
from re import search
from typing import Optional, Type

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.helpers.api import HTTPExceptionModel
from app.helpers.exceptions import ObjectNotFound, ServiceUnavailable


def add_exception_handler(
    app: FastAPI, exception: Type[Exception], error_message: str, status_code: int, headers: Optional[dict] = None
) -> None:
    """
    Добавление обработчика ошибок
    :param app:               объект fast_api
    :param exception:         ошибка
    :param error_message:     сообщение
    :param status_code:       статус код
    :param headers:           хедеры
    """

    @app.exception_handler(exception)
    async def exception_handler(_request: Request, _exc: exception):
        return JSONResponse(
            status_code=status_code, content=HTTPExceptionModel(detail=error_message).dict(), headers=headers
        )


def add_object_not_found_handler(app: FastAPI, headers: Optional[dict] = None):
    @app.exception_handler(ObjectNotFound)
    async def exception_handler(_request: Request, exc: ObjectNotFound):
        return JSONResponse(status_code=404, content=HTTPExceptionModel(detail=str(exc)).dict(), headers=headers)


def add_object_service_unavailable_handler(app: FastAPI, headers: Optional[dict] = None):
    @app.exception_handler(ServiceUnavailable)
    async def exception_handler(_request: Request, exc: ServiceUnavailable):
        return JSONResponse(status_code=500, content=HTTPExceptionModel(detail=str(exc)).dict(), headers=headers)


def add_unique_violation_handler(app: FastAPI, headers: Optional[dict] = None):
    warnings.warn("Устарел, необходимо использовать add_integrity_errors_handler", DeprecationWarning)
    from sqlalchemy.exc import IntegrityError

    @app.exception_handler(IntegrityError)
    async def exception_handler(_request: Request, exc: IntegrityError):
        if exc.orig.pgcode == "23505":
            return JSONResponse(
                status_code=400,
                content=HTTPExceptionModel(detail="Такой объект уже существует").dict(),
                headers=headers,
            )
        raise exc


def add_integrity_errors_handler(app: FastAPI, headers: Optional[dict] = None):
    from sqlalchemy.exc import IntegrityError

    @app.exception_handler(IntegrityError)
    async def exception_handler(_request: Request, exc: IntegrityError):
        if exc.orig.pgcode == "23505":
            return JSONResponse(
                status_code=400,
                content=HTTPExceptionModel(detail="Такой объект уже существует").dict(),
                headers=headers,
            )
        if exc.orig.pgcode == "23503":
            if field_name := search(r"DETAIL: {2}Key \((?P<field_name>.*)\)=", str(exc)):
                field_name = field_name.group("field_name")
                return JSONResponse(
                    status_code=400,
                    content=HTTPExceptionModel(detail=f"Не найден объект с таким {field_name}").dict(),
                    headers=headers,
                )
        raise exc
