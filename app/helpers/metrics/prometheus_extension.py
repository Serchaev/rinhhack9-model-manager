from fastapi import FastAPI
from prometheus_client import make_asgi_app


def add_prometheus_extension(app: FastAPI) -> None:
    """
    Функция добавление прометеуса
    """
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
