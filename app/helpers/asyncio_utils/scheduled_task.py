import asyncio
import logging
from asyncio import TimeoutError, sleep, wait_for
from typing import Optional

from tenacity import retry, wait_random


def scheduled_task(
    coro_or_future: callable,
    repeat_timeout: int,
    task_timeout: Optional[float] = None,
    logger: logging.Logger = None,
) -> asyncio.Task:
    """
    :param coro_or_future:      функция возвращающая awaitable объект
    :param repeat_timeout:      время повтора
    :param task_timeout:        Максимальное время выполнения задачи
    :param loop:                текущий цикл
    :param logger:              Логгинг
    :return:                    None
    """
    logger = logger or logging

    async def repeat():
        while True:
            try:
                await wait_for(coro_or_future(), timeout=task_timeout)
            except TimeoutError:
                logger.error(f"Task {coro_or_future.__name__} timed out after {task_timeout} seconds.")
            except Exception as e:
                raise e
            await sleep(repeat_timeout)

    return asyncio.create_task(retry(wait=wait_random(min=1, max=10))(repeat)())
