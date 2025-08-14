import json
from typing import Optional

from scipy import signal

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class Resample(Operator):
    def __init__(self, opID: int):
        super(Resample, self).__init__(opID, 1, 1)

        self.sampleRate = 0

    def setData(self, data: json):
        self.sampleRate = data["sampleRate"]

    def getData(self) -> dict:
        return {"sampleRate": self.sampleRate}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        audioSignal = tupleIn.data[0]

        newData = signal.resample(audioSignal.data, self.sampleRate)

        return self.createTuple((Signal(self.sampleRate, newData.tolist()),))
