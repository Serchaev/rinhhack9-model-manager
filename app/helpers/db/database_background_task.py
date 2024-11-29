import asyncio
import logging
from functools import partial

from sqlalchemy import text

from app.helpers.asyncio_utils import scheduled_task
from app.helpers.db import SessionManager


async def partition_maintenance(session_manager: SessionManager, logger: logging.Logger) -> None:
    logger.info("Запуск partman.run_maintenance...")
    async with session_manager.async_session_factory() as session:
        await session.execute(text("SELECT partman.run_maintenance();"))
    logger.info("Запуск partman.run_maintenance прошёл успешно")


def partitions_task(
    session_manager: SessionManager,
    repeat_timeout: int,
    logger: logging.Logger = None,
) -> asyncio.Task:
    logger = logger or logging

    task = scheduled_task(
        partial(partition_maintenance, session_manager=session_manager, logger=logger), repeat_timeout
    )
    logger.info("Инициализация автоматического управления партициями прошла успешно")
    return task


async def refresh_material_view(
    material_view_name: str, session_manager: SessionManager, logger: logging.Logger
) -> None:
    logger.info(f"Запуск обновления {material_view_name}")
    async with session_manager.async_session_factory() as session:
        await session.execute(text(f"REFRESH MATERIALIZED VIEW {material_view_name}"))
    logger.info(f"Запуск обновления {material_view_name} прошло успешно")


async def refresh_material_view_task(
    material_view_name: str,
    session_manager: SessionManager,
    repeat_timeout: int,
    logger: logging.Logger = None,
) -> asyncio.Task:
    logger = logger or logging

    task = scheduled_task(
        partial(
            refresh_material_view, material_view_name=material_view_name, session_manager=session_manager, logger=logger
        ),
        repeat_timeout,
    )
    logger.info(f"Инициализация задачи обновления {material_view_name} прошла успешно")
    return task
