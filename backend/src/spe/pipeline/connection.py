from __future__ import annotations
from typing import TYPE_CHECKING
from spe.common.tuple import Tuple
from streamVizzard import StreamVizzard

if TYPE_CHECKING:
    from spe.pipeline.socket import Socket


class Connection:
    def __init__(self, conID: int, socketIN: Socket, socketOUT: Socket):
        self.id = conID  # Unique system wide
        self.input = socketIN
        self.output = socketOUT

        if StreamVizzard.getConfig().MONITORING_ENABLED:
            from spe.runtime.monitor.connectionMonitor import ConnectionMonitor
            self._monitor = ConnectionMonitor(self)
        else:
            self._monitor = None

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
