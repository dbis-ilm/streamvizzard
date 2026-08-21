from typing import Dict

from spe.pipeline.operators.base.sources.socketServer import SocketServer

from utils.utils import escapeStr


class TextSocketServer(SocketServer):
    def __init__(self,  opID: int):
        super(TextSocketServer, self).__init__(opID)

        self.delimiter = "\n"
        self.encoding = "utf-8"

        self._internalBuffer = ""

    def setData(self, data: Dict):
        data["maxBytes"] = 8192  # Fixed default value
        super().setData(data)

        self.delimiter = escapeStr(data["delimiter"], False)
        self.encoding = data["encoding"]

    def getData(self) -> dict:
        d = super().getData()

        del d["maxBytes"]
        d["delimiter"] = escapeStr(self.delimiter, True)
        d["encoding"] = self.encoding

        return d

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
