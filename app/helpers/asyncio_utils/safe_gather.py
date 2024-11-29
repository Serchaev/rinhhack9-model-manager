from asyncio import Semaphore, gather


async def run_with_semaphore(semaphore: Semaphore, coro):
    """
    Вызвать функцию с учётом семафора
    :param semaphore:       Semaphore
    :param coro:            корутина
    """
    async with semaphore:
        return await coro


async def safe_gather(
    *coros_or_futures,
    parallelism_size: int = 10,
    return_exceptions: bool = False,
):
    """
    Gather с учётом parallelism_size
    :param coros_or_futures:        корутины или features
    :param parallelism_size:        лимит параллельно выполняемых корутин
    :param return_exceptions:       если True то исключения передаются вместе с результатами, False то возвращает ошибку
    """
    semaphore = Semaphore(value=parallelism_size)
    coroutines = [run_with_semaphore(semaphore, task) for task in coros_or_futures]
    return await gather(*coroutines, return_exceptions=return_exceptions)
