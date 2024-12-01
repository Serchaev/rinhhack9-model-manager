from functools import partial

from starlette.middleware.base import BaseHTTPMiddleware

from app.amqp.model_consumer import model_on_message
from app.api.routers.predict_router import router as predict_router
from app.config import settings
from app.container import Container
from app.helpers.api import (
    Server,
    add_health_check_router,
    add_object_not_found_handler,
)
from app.helpers.interfaces import AmqpAbc
from app.helpers.metrics import MetricsMiddleware, add_prometheus_extension
from app.helpers.optimization import ujson_enable


async def start_amqp(amqp_client: AmqpAbc = Container.amqp_client()):
    await amqp_client.init_queue(settings.AMQP.routing_keys.model_manager_routing_key)
    await amqp_client.init_consumer(settings.AMQP.routing_keys.model_manager_routing_key, model_on_message)


ujson_enable()
app = Server(
    name=settings.NAME,
    version=settings.VERSION,
    description="Backend service",
    logging_config=settings.LOGGING,
    cors_config=settings.CORS,
    routers=[predict_router],
    middlewares=[MetricsMiddleware(BaseHTTPMiddleware)],
    start_callbacks=[start_amqp],
    stop_callbacks=[Container.redis().close],
    exception_handlers=[add_object_not_found_handler],
    extensions=[
        partial(
            add_health_check_router,
            service=settings.NAME,
            version=settings.VERSION,
            branch=settings.BRANCH,
            commit=settings.COMMIT,
        ),
        add_prometheus_extension,
    ],
).app
