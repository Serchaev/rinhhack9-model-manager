from app.helpers.container import providers
from app.helpers.db import SessionManager
from app.helpers.redis import RedisStreamAmqp, RedisQueueAmqp
from redis.asyncio.client import Redis

from app.config import settings


class Container:
    redis = providers.Singleton(
        Redis,
        host=settings.REDIS.host,
        port=settings.REDIS.port,
        username=settings.REDIS.login,
        password=settings.REDIS.password,
        decode_responses=True,
        db=settings.REDIS.database,
    )
    amqp_client = providers.Singleton(
        RedisQueueAmqp,
        redis=redis(),
    )
    session_manager = providers.Singleton(
        SessionManager,
        dialect=settings.POSTGRES.dialect,
        host=settings.POSTGRES.host,
        login=settings.POSTGRES.login,
        password=settings.POSTGRES.password,
        port=settings.POSTGRES.port,
        database=settings.POSTGRES.database,
        echo=settings.POSTGRES.echo,
        service_name=settings.NAME,
        pool_size=settings.POSTGRES.pool_min_size,
        max_overflow=settings.POSTGRES.pool_max_size,
        pool_timeout=settings.POSTGRES.pool_timeout,
    )
