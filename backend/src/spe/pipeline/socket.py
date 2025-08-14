from __future__ import annotations
from typing import TYPE_CHECKING
from typing import List

if TYPE_CHECKING:
    from spe.pipeline.connection import Connection
    from spe.pipeline.operators.operator import Operator


class Socket:
    def __init__(self, op: Operator, socketID: int, inSocket: bool = False):
        self.op = op
        self.id = socketID
        self.inSocket = inSocket
        self._connections: List[Connection] = list()

    def addConnection(self, connection: Connection):
        self._connections.append(connection)

    def removeConnection(self, connection: Connection):
        for i in range(len(self._connections)):
            if self._connections[i] == connection:
                del self._connections[i]
                return

    def clearConnections(self):
        self._connections.clear()

    def hasConnections(self) -> bool:
        return len(self._connections) > 0

    def getConnections(self) -> List[Connection]:
        return self._connections

    def updateConnection(self, conID: int, connection: Connection):
        for i in range(len(self._connections)):
            if self._connections[i].id == conID:
                self._connections[i] = connection
                return
