from typing import Optional, Dict

from spe.common.dataType import StringType
from spe.pipeline.operators.base.sinks.socketServer import SocketServer
from spe.pipeline.operators.sink import Sink
from spe.common.tuple import Tuple


@Sink.requiresInput(StringType())
class TextSocketServer(SocketServer):
    def __init__(self, opID: int):
        super().__init__(opID)

        self.encoding = "utf-8"

    def setData(self, data: Dict):
        super().setData(data)

        self.encoding = data["encoding"]

    def getData(self) -> dict:
        d = super().getData()
        d["encoding"] = self.encoding

        return d

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self._ensureClientConnection()

        self._socket.writeData(str(tupleIn.data[0]).encode(self.encoding))

        return self.createSinkTuple()
