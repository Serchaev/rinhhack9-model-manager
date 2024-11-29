import asyncio
import logging
import logging.config
import os
from multiprocessing import Process
from typing import Optional

from setproctitle import setproctitle


class SupervisorSubProcess:
    def __init__(
        self,
        target,
        name: str,
        process_count: int,
        target_args: Optional[tuple] = None,
        target_kwargs: Optional[dict] = None,
        **kwargs,
    ):
        self.name = name
        self.process_count = process_count
        self.target = target
        self.target_args = target_args or ()
        self.target_kwargs = target_kwargs or {}

    def create_process(self, service_name: str) -> Process:
        process = Process(
            target=self.run,
            args=(self.target, service_name, self.name, *self.target_args),
            kwargs=self.target_kwargs,
        )
        return process

    @classmethod
    def run(cls, target, service_name: str, subprocess_name: str, *args, **kwargs):
        name = f"{service_name}::{subprocess_name}"
        pid = os.getpid()
        setproctitle(name)
        logging.info(f"Запущен процесс {name}, pid {pid}")

        try:
            if asyncio.iscoroutinefunction(target):
                asyncio.run(target(*args, **kwargs))
            else:
                target(*args, **kwargs)
        finally:
            logging.info(f"Завершён процесс {name}, pid {pid}")
