import logging
import logging.config
from multiprocessing import Pipe, Process
from time import sleep

from setproctitle import setproctitle
from tenacity import retry, wait_random

from app.helpers.supervisor.healthcheck_app import start_app
from app.helpers.supervisor.supervisor_subprocess import SupervisorSubProcess


class Supervisor:
    def __init__(
        self,
        name: str,
        logging_config: dict,
        supervisor_subprocesses: list[SupervisorSubProcess],
        timeout_periodicity: int = 1,
    ):
        self.process = None

        self.name = name
        self.logging_config = logging_config

        self.supervisor_subprocesses = {
            supervisor_subprocess.name: supervisor_subprocess for supervisor_subprocess in supervisor_subprocesses
        }
        self._supervisor_processes = {
            supervisor_subprocess.name: [] for supervisor_subprocess in supervisor_subprocesses
        }
        self.timeout_periodicity = timeout_periodicity
        self.supervisor_pipe_conn, self.server_pipe_conn = Pipe()
        self._init_logger()

    def _init_logger(self) -> None:
        logging.config.dictConfig(self.logging_config)
        logging.info("Инициализация logger прошла успешно")

    def start_healthcheck_app(
        self,
        service: str,
        version: str,
        branch: str,
        commit: str,
        host: str,
        port: int,
        recv_timeout: int = 10,
    ):
        Process(
            target=start_app,
            args=(
                service,
                version,
                branch,
                commit,
                host,
                port,
                self.server_pipe_conn,
                recv_timeout,
                self.supervisor_subprocesses,
            ),
        ).start()

    @staticmethod
    def check_live_process(process: Process) -> bool:
        try:
            is_alive = process.is_alive()
        except ValueError:
            is_alive = False
        return is_alive

    @retry(wait=wait_random(min=1, max=10))
    def _run(self):
        setproctitle(f"{self.name}::supervisor")
        while True:
            history_data = list()
            for supervisor_process_name in self._supervisor_processes.keys():
                self._supervisor_processes[supervisor_process_name] = [
                    p for p in self._supervisor_processes[supervisor_process_name] if self.check_live_process(p)
                ]
                logging.debug(
                    " ".join(
                        [
                            "Имя процесса: {0}.".format(supervisor_process_name),
                            "Кол-во запланированных процессов: {0}.".format(
                                self.supervisor_subprocesses[supervisor_process_name].process_count
                            ),
                            "Кол-во живых процессов: {0}.".format(
                                len(self._supervisor_processes[supervisor_process_name])
                            ),
                        ]
                    )
                )
                supervisor_subprocess: SupervisorSubProcess = self.supervisor_subprocesses[supervisor_process_name]
                history_data.append(
                    {
                        "status": True,
                        "name": supervisor_process_name,
                        "processes_num_plan": self.supervisor_subprocesses[supervisor_process_name].process_count,
                        "processes_num_alive": len(self._supervisor_processes[supervisor_process_name]),
                    }
                )
                while len(self._supervisor_processes[supervisor_process_name]) < supervisor_subprocess.process_count:
                    subprocess: Process = supervisor_subprocess.create_process(self.name)
                    subprocess.start()
                    self._supervisor_processes[supervisor_process_name].append(subprocess)

            if self.supervisor_pipe_conn.poll():
                self.supervisor_pipe_conn.recv()
                self.supervisor_pipe_conn.send(history_data)
            if len(history_data) >= 10:
                history_data.pop(0)
            sleep(self.timeout_periodicity)

    def run(self, block=False):
        self.process = Process(target=self._run)
        self.process.start()
        if block:
            self.process.join()
