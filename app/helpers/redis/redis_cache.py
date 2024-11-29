import asyncio
import functools
import logging
import pickle
from typing import Any, overload

from redis.asyncio import Redis

from app.helpers.asyncio_utils import run_with_timeout


class RedisCache:
    def __init__(
        self,
        redis: Redis,
        logger: logging.Logger = None,
        serializer=pickle,
    ):
        self.redis = redis
        self.logger = logger or logging
        self.serializer = serializer

    async def set(self, key, value, timeout, expire) -> None:
        func = self.redis.set(key, self.serializer.dumps(value), ex=expire)
        await run_with_timeout(func, timeout=timeout, operation_name="RedisCache Set", logger=self.logger)

    async def get(self, key, timeout) -> Any:
        result = await run_with_timeout(
            self.redis.get(key),
            timeout=timeout,
            operation_name="RedisCache Get",
            logger=self.logger,
        )
        return self.serializer.loads(result) if result else None

    @overload
    def cache(self, func, ttl=60, timeout=0.07, *args, **kwargs) -> Any:
        """
        Кешировать результат функции
        :param func: функция
        :param ttl: время жизни кеша в секундах
        :param timeout: время ожидания ответа от redis в секундах
        """
        ...

    @overload
    def cache(self, ttl: float = 60, timeout: float = 0.07) -> callable:
        """
        Декоратор для кеширования функции
        :param ttl: время жизни кеша в секундах
        :param timeout: время ожидания ответа от redis в секундах
        """
        ...

    def cache(self, ttl: float = 60, timeout: float = 0.07, *args, **kwargs):
        if func_cached := kwargs.pop("func", None):
            if asyncio.iscoroutinefunction(func_cached):
                return self._cache_impl(func=func_cached, *args, timeout=timeout, expire=ttl, **kwargs)
            return asyncio.get_event_loop().run_until_complete(
                self._cache_impl(func=func_cached, *args, timeout=timeout, expire=ttl, **kwargs)
            )

        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*local_args, **local_kwargs):
                return await self._cache_impl(func, *local_args, timeout=timeout, expire=ttl, **local_kwargs)

            @functools.wraps(func)
            def sync_wrapper(*local_args, **local_kwargs):
                return asyncio.get_event_loop().run_until_complete(
                    self._cache_impl(func, *local_args, timeout=timeout, expire=ttl, **local_kwargs)
                )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    async def _cache_impl(self, func, *args, timeout, expire, **kwargs) -> Any:
        cache_key = self._make_key(func, args, kwargs)
        cached_value = await self.get(key=cache_key, timeout=timeout)
        if cached_value:
            return cached_value

        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        await self.set(key=cache_key, value=result, expire=expire, timeout=timeout)

        return result

    @staticmethod
    def _make_key(func, args, kwargs) -> str:
        return f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
