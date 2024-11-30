import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix=False,
    environments=True,
    settings_files=["settings.yml"],
)

PROJECT_PATH = str(Path(__file__).parent.parent.resolve())
try:
    with open(os.path.join(PROJECT_PATH, ".commit"), "r", encoding="utf-8") as file:
        settings.VERSION = file.readline().rstrip("\n")
        settings.BRANCH = file.readline().rstrip("\n")
        settings.COMMIT = file.readline().rstrip("\n")
except FileNotFoundError:
    with open(os.path.join(PROJECT_PATH, "pyproject.toml"), encoding="utf-8") as file:
        file_data = file.read()
    settings.VERSION = re.search(r'version = "(?P<version>\d+.\d+.\d+)"', file_data).group("version")
    settings.COMMIT = ""
    settings.BRANCH = ""


DB_URL_WITH_ALEMBIC = (
    f"postgresql+psycopg2://{settings.POSTGRES.login}:{settings.POSTGRES.password}@"
    f"{settings.POSTGRES.host}:{settings.POSTGRES.port}/{settings.POSTGRES.database}"
)


def get_file_handler(file_name: str) -> RotatingFileHandler:
    file_handler = RotatingFileHandler(
        filename=file_name,
        maxBytes=5242880,
        backupCount=10,
    )
    file_handler.setFormatter(logging.Formatter(settings.LOGGER.format))
    return file_handler


def get_stream_handler() -> logging.StreamHandler:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(settings.LOGGER.format))
    return stream_handler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    os.makedirs(settings.LOGGER.dir_path, exist_ok=True)
    file_path = str(
        Path().cwd().joinpath(settings.LOGGER.dir_path, "logs.log"),
    )
    handler_1 = get_file_handler(file_name=file_path)
    handler_2 = get_stream_handler()
    if not logger.hasHandlers():
        for handler in [handler_1, handler_2]:
            logger.addHandler(handler)
    logger.setLevel(settings.LOGGER.level)
    return logger
