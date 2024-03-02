import copy
import uuid
from typing import TYPE_CHECKING

from pympler import asizeof

from spe.runtime.runtimeCommunicator import getRuntimeManager
from spe.runtime.structures.timer import Timer

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator


class Tuple:
    def __init__(self, data: tuple, operator):
        self.uuid = str(uuid.uuid4().hex)

        self.data: tuple = data

        self.operator: Operator = operator

        self.eventTime = Timer.currentTime()  # Time when this specific tuple was created

        self.socketID: int = 0  # Always the IN socket of the operator that processes the tuple

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
        # Returns bytes

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
