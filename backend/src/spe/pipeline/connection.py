from __future__ import annotations
from typing import TYPE_CHECKING
from spe.common.tuple import Tuple
from spe.runtime.monitor.connectionMonitor import ConnectionMonitor
from streamVizzard import StreamVizzard

if TYPE_CHECKING:
    from spe.pipeline.socket import Socket


class Connection:
    def __init__(self, conID: int, socketIN: Socket, socketOUT: Socket):
        self.id = conID  # Unique system wide
        self.input = socketIN
        self.output = socketOUT

        self._monitor = ConnectionMonitor(self) if StreamVizzard.getConfig().MONITORING_ENABLED else None

    def onTupleTransmitted(self, origTuple: Tuple):
        if self._monitor is not None:
            self._monitor.registerTuple(origTuple)

    def getMonitor(self):
        return self._monitor

    @staticmethod
    def create(conID: int, socketIN: Socket, socketOUT: Socket) -> Connection:
        newCon = Connection(conID, socketIN, socketOUT)
        socketIN.addConnection(newCon)
        socketOUT.addConnection(newCon)

        return newCon
