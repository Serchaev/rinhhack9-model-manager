from functools import partial
from multiprocessing.connection import Connection

import uvicorn
from fastapi import APIRouter, Depends

from app.helpers.api.common_types import ProcessStatusOut
from app.helpers.api.health_check import add_health_check_router
from app.helpers.api.server import Server
from app.helpers.supervisor.supervisor_subprocess import SupervisorSubProcess


class HealthCheckApp:

    def __init__(
        self,
        service: str,
        version: str,
        branch: str,
        commit: str,
        pipe_conn: Connection,
        recv_timeout: int,
        supervisor_subprocesses: dict[str:SupervisorSubProcess],
    ) -> None:
        self.service = service
        self.version = version
        self.branch = branch
        self.commit = commit
        self.pipe_conn = pipe_conn
        self.recv_timeout = recv_timeout
        self.supervisor_subprocesses = supervisor_subprocesses
        api_router = self.get_api_router()
        self.app = Server(
            name=self.service,
            version=self.version,
            routers=[api_router],
            extensions=[
                partial(
                    add_health_check_router,
                    service=self.service,
                    version=self.version,
                    branch=self.branch,
                    commit=self.commit,
                )
            ],
            stop_callbacks=[self.pipe_conn.close],
        ).app

    def get_api_router(self):
        api_router = APIRouter(prefix="/healthcheck/status", tags=["Status"])

        @api_router.get("", response_model=list[ProcessStatusOut])
        def get_healthcheck_status(
            pipe_conn: Connection = Depends(lambda: self.pipe_conn),
            recv_timeout: int = Depends(lambda: self.recv_timeout),
            supervisor_subprocesses: dict[str:SupervisorSubProcess] = Depends(lambda: self.supervisor_subprocesses),
        ):
            pipe_conn.send(True)
            if pipe_conn.poll(timeout=recv_timeout):
                process_status = pipe_conn.recv()
                process_status = [ProcessStatusOut.model_validate(status) for status in process_status]
                return process_status
            else:
                process_status: list[ProcessStatusOut] = list()
                for process in supervisor_subprocesses.values():
                    status = ProcessStatusOut(
                        status=False, name=process.name, processes_num_plan=process.process_count, processes_num_alive=0
                    )
                    process_status.append(status)
                return process_status

        return api_router


def start_app(
    service: str,
    version: str,
    branch: str,
    commit: str,
    host: str,
    port: int,
    server_pipe_conn: Connection,
    recv_timeout: int,
    supervisor_subprocesses: dict[str:SupervisorSubProcess],
):
    app = HealthCheckApp(
        service=f"{service}::healthcheck",
        version=version,
        branch=branch,
        commit=commit,
        pipe_conn=server_pipe_conn,
        recv_timeout=recv_timeout,
        supervisor_subprocesses=supervisor_subprocesses,
    ).app
    uvicorn.run(app=app, host=host, port=port)
