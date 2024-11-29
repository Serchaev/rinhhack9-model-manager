from asyncio import AbstractEventLoop, get_event_loop
from concurrent.futures import Executor
from functools import partial
from typing import Any, Optional


async def run_in_executor(
    func: callable, loop: Optional[AbstractEventLoop] = None, executor: Optional[Executor] = None, *args, **kwargs
) -> Any:
    """
    :param func:        функция
    :param loop:        текущий цикл
    :param executor:    свой executor, если нужно ограничить параллельность
    :param args:        дополнительный порядковые параметры
    :param kwargs:      дополнительные именованные параметры
    :return:            результат функции func
    """
    loop = loop or get_event_loop()
    return await loop.run_in_executor(executor, partial(func, *args, **kwargs))
