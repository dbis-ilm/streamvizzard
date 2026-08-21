import threading
from typing import Optional, Dict

from spe.common.dataType import BytesType
from spe.pipeline.operators.base.sources.socketServer import SocketServerImpl
from spe.pipeline.operators.sink import Sink
from spe.common.tuple import Tuple


@Sink.requiresInput(BytesType())
class SocketServer(Sink):
    def __init__(self, opID: int):
        super().__init__(opID, 1)

        self._socket = SocketServerImpl()

        self._clientConnectionThread: Optional[threading.Thread] = None

    def setData(self, data: Dict):
        ipOrPortChanged = (self._socket.port != data["port"]) or (self._socket.ip != data["ip"])

        self._socket.port = data["port"]
        self._socket.ip = data["ip"]

        if ipOrPortChanged:
            self._socket.close()

    def getData(self) -> dict:
        return {"port": self._socket.port, "ip": self._socket.ip}

    def onRuntimeDestroy(self):
        super(SocketServer, self).onRuntimeDestroy()

        if self._socket is not None:
            self._socket.close()

    def _ensureClientConnection(self):
        # Start client listen thread in background if we have no client yet

        if not self._socket.hasConnection() and self._clientConnectionThread is None:
            self._clientConnectionThread = threading.Thread(target=self._listenForClientConnection, daemon=True)
            self._clientConnectionThread.start()

    def _listenForClientConnection(self):
        self._socket.ensureConnection()  # Returns if socket is closed, so reconnect is possible

        self._clientConnectionThread = None

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self._ensureClientConnection()

        self._socket.writeData(tupleIn.data[0])

        return self.createSinkTuple()
