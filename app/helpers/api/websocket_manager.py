import logging
from asyncio import iscoroutinefunction, sleep, wait_for
from typing import Optional, Union
from uuid import uuid4

from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from websockets.exceptions import ConnectionClosedOK

from app.helpers.asyncio_utils import safe_gather
from app.helpers.interfaces import WebsocketManagerAbc


class WebsocketManager(WebsocketManagerAbc):
    def __init__(self, logger: logging.Logger = None):
        self.connections = {}
        self.logger = logger or logging

    async def connect(self, websocket: WebSocket, connection_id: Optional[str] = None) -> str:
        await websocket.accept()
        connection_id = connection_id or str(uuid4())
        self.connections[connection_id] = websocket
        self.logger.info("Подключен websocket id: %s", connection_id)
        self.logger.debug("Кол-во активных websockets: %s", len(self.connections))
        return connection_id

    async def disconnect(self, connection_id: str) -> bool:
        websocket = self.connections.pop(connection_id, None)
        if not websocket:
            return False
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
        self.logger.info("Отключен websocket id: %s", connection_id)
        self.logger.debug("Кол-во активных websocket: %s", len(self.connections))
        return True

    async def send(self, message: Union[str, dict, list, bytes], connection_id: str) -> None:
        websocket = self.connections.get(connection_id, None)
        if not websocket:
            raise WebSocketDisconnect(reason=f"Websocket с id: {connection_id} не подключён")
        self.logger.debug("Отправка сообщения по websocket id: %s...", connection_id)
        if isinstance(message, str):
            await websocket.send_text(message)
        elif isinstance(message, bytes):
            await websocket.send_bytes(message)
        elif isinstance(message, (dict, list)):
            await websocket.send_json(message)
        else:
            raise TypeError("Неподдерживаемый тип сообщения")
        self.logger.debug("Отправка сообщения по websocket id: %s прошла успешно", connection_id)

    async def receive(self, connection_id: str, timeout: Optional[float] = None) -> str:
        websocket = self.connections.get(connection_id, None)
        if not websocket:
            raise WebSocketDisconnect(reason=f"Websocket с id: {connection_id} не подключён")
        self.logger.debug("Получение сообщения по websocket id: %s", connection_id)
        response = await wait_for(websocket.receive(), timeout=timeout)
        self.logger.debug("Получение сообщения по websocket id: %s прошло успешно", connection_id)
        return response["text"]

    async def broadcast(self, message: Union[str, dict, list, bytes]) -> None:
        await safe_gather(
            *[self.send(message=message, connection_id=connection_id) for connection_id in self.connections.keys()],
            parallelism_size=10,
            return_exceptions=True,
        )

    async def ping(self, connection_id) -> bool:
        try:
            await self.send(b"", connection_id)
            return True
        except Exception:
            return False

    async def websocket_handler(self, connection_id: str, func: callable, repeat_timeout: float = 1):
        try:
            while True:
                if not await self.ping(connection_id):
                    raise WebSocketDisconnect(reason=f"Websocket с id: {connection_id} отключён")
                if iscoroutinefunction(func):
                    await func()
                else:
                    func()
                await sleep(repeat_timeout)
        except (WebSocketDisconnect, ConnectionClosedOK):
            self.logger.info("Получен сигнал отключения websocket id: %s", connection_id)
        finally:
            await self.disconnect(connection_id)
