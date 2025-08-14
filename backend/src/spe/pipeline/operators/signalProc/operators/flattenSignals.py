import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.pipeline.operators.signalProc.dataTypes.signal import Signal
from spe.common.tuple import Tuple


class FlattenSignals(Operator):
    def __init__(self, opID: int):
        super(FlattenSignals, self).__init__(opID, 1, 1)

    def setData(self, data: json):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        signalList = tupleIn.data[0]

        if len(signalList) == 0:
            return None

        totalSignals = []

        for signal in signalList:
            totalSignals += signal.data

        return self.createTuple((Signal(signalList[0].samplingRate, totalSignals),))
