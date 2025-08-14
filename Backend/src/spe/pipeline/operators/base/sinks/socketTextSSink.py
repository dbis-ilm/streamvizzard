import json
import threading
from typing import Optional

from spe.pipeline.operators.base.sources.socketServer import SocketServerImpl
from spe.pipeline.operators.sink import Sink
from spe.common.tuple import Tuple

# TODO: CHECK IF WE CAN START SOCKET ON RUNTIMECREATE!


class SocketTextSSink(Sink):
    def __init__(self, opID: int):
        super().__init__(opID, 1)

        self._socket = SocketServerImpl()
        self._socket.maxBytes = 8192  # Fixed default value

        self._clientConnectionThread: Optional[threading.Thread] = None

        self.encoding = "utf-8"

    def setData(self, data: json):
        ipOrPortChanged = (self._socket.port != data["port"]) or (self._socket.ip != data["ip"])

        self._socket.port = data["port"]
        self._socket.ip = data["ip"]
        self.encoding = data["encoding"]

        if ipOrPortChanged:
            self._socket.close()

    def getData(self) -> dict:
        return {"port": self._socket.port, "ip": self._socket.ip, "encoding": self.encoding}

    def onRuntimeDestroy(self):
        super(SocketTextSSink, self).onRuntimeDestroy()

        if self._socket is not None:
            self._socket.close()

    def _checkConnectionStatus(self):
        # Start client listen thread in background if we have no client yet

        if not self._socket.hasConnection() and self._clientConnectionThread is None:
            self._clientConnectionThread = threading.Thread(target=self._listenForClientConnection, daemon=True)
            self._clientConnectionThread.start()

    def _listenForClientConnection(self):
        self._socket.awaitConnection()  # Returns if socket is closed

        self._clientConnectionThread = None

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self._checkConnectionStatus()

        self._socket.writeData(str(tupleIn.data[0]).encode(self.encoding))

        return self.createErrorTuple()
