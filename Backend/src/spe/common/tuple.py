from __future__ import annotations
import copy
import uuid
from enum import Enum
from typing import TYPE_CHECKING

from pympler import asizeof

from spe.runtime.runtimeGateway import getRuntimeManager
from spe.common.timer import Timer

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator


class Tuple:
    class State(Enum):
        DATA = 0  # Default tuples that are processed and traversed through the pipeline
        SINK = 1  # Sink tuples, forwarded but not transmitted
        ERROR = 2  # Discarded from the system without forwarding
        DROPPED = 3  # Discarded from the system without forwarding

    def __init__(self, data: tuple, operator: Operator, state: State = State.DATA):
        self.uuid = str(uuid.uuid4().hex)

        self.data = data

        self.operator = operator

        self.eventTime = Timer.currentTime()  # Time when this specific tuple was created

        self.socketID: int = 0  # Always the IN socket of the operator that processes the tuple

        self.state = state

    def __copy__(self):
        return self.clone(False)

    def __deepcopy__(self, memo):
        return self.clone(True)

    def clone(self, deep: bool = False):
        t = Tuple(self.data, self.operator)
        t.eventTime = self.eventTime
        t.socketID = self.socketID
        t.uuid = self.uuid

        if deep:
            t.data = copy.deepcopy(self.data)

        return t

    def calcMemorySize(self) -> int:
        """ Returns amount of bytes in this data tuple. """

        if self.data is None:
            return 0

        totalSize = 0

        for i in range(0, len(self.data)):
            d = self.data[i]
            totalSize += d.getDataSize() if hasattr(d, "getDataSize") else asizeof.asizeof(d)

        return totalSize

    def __getstate__(self):
        return {"opID": self.operator.id, "uuid": self.uuid,
                "data": self.data, "eventTime": self.eventTime,
                "socketID": self.socketID}

    def __setstate__(self, d):
        self.data = d["data"]
        self.eventTime = d["eventTime"]
        self.uuid = d["uuid"]
        self.socketID = d["socketID"]
        self.operator = getRuntimeManager().getPipeline().getOperator(d["opID"])

    @staticmethod
    def createSinkTuple(operator: Operator) -> Tuple:
        return Tuple((), operator, state=Tuple.State.SINK)

    @staticmethod
    def createErrorTuple(operator: Operator) -> Tuple:
        return Tuple((), operator, state=Tuple.State.ERROR)

    @staticmethod
    def createDroppedTuple(operator: Operator) -> Tuple:
        return Tuple((), operator, state=Tuple.State.DROPPED)

    def isValidTuple(self):
        return self.isDataTuple() or self.isSinkTuple()

    def isDataTuple(self):
        return self.state == Tuple.State.DATA

    def isSinkTuple(self):
        return self.state == Tuple.State.SINK

    def isErrorTuple(self):
        return self.state == Tuple.State.ERROR

    def isDroppedTuple(self):
        return self.state == Tuple.State.DROPPED
