import json
from typing import List

from spe.pipeline.operators.base.sources.socketServer import SocketServer
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs

from utils.utils import escapeStr

# TODO: CHECK IF WE CAN START SOCKET ON RUNTIMECREATE!


class SocketTextSSource(SocketServer):
    def __init__(self,  opID: int):
        super(SocketTextSSource, self).__init__(opID)

        self.delimiter = "\n"
        self.encoding = "utf-8"

        self._socket.maxBytes = 8192  # Fixed default value

        self._internalBuffer = ""

    def setData(self, data: json):
        ipOrPortChanged = (self._socket.port != data["port"]) or (self._socket.ip != data["ip"])

        self._socket.port = data["port"]
        self._socket.ip = data["ip"]
        self.delimiter = escapeStr(data["delimiter"], False)
        self.encoding = data["encoding"]

        if ipOrPortChanged:
            self._socket.close()

    def getData(self) -> dict:
        return {"port": self._socket.port, "ip": self._socket.ip, "delimiter": escapeStr(self.delimiter, True), "encoding": self.encoding}

    def _onDataReceived(self, data: bytes):
        text = data.decode(self.encoding)

        self._internalBuffer += text

        # Iterates and extracts all data elements separated by the delimiter

        while True:
            idx = self._internalBuffer.find(self.delimiter)

            if idx > -1:
                data = self._internalBuffer[:idx]

                self._internalBuffer = self._internalBuffer[idx + 1:]

                self._produce((data,))
            else:
                break

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        return [CompileOpSpecs.getSVDefault()]
