from __future__ import annotations
from typing import TYPE_CHECKING
import config
from spe.runtime.structures.tuple import Tuple
from spe.runtime.monitor.connectionMonitor import ConnectionMonitor

if TYPE_CHECKING:
    from spe.pipeline.socket import Socket
    from spe.pipeline.pipeline import Pipeline


class Connection:
    def __init__(self, conID: int, socketIN: Socket, socketOUT: Socket):
        self.id = conID  # Unique system wide
        self.input = socketIN
        self.output = socketOUT

        self._monitor = ConnectionMonitor(self) if config.MONITORING_ENABLED else None

    def onTupleTransmitted(self, origTuple: Tuple):
        if self._monitor is not None:
            self._monitor.registerTuple(origTuple)

    def getMonitor(self):
        return self._monitor

    @staticmethod
    def create(pipeline: Pipeline, conID: int, socketIN: Socket, socketOUT: Socket) -> Connection:
        newCon = Connection(conID, socketIN, socketOUT)
        socketIN.addConnection(newCon)
        socketOUT.addConnection(newCon)

        pipeline.registerConnection(newCon)

        return newCon
