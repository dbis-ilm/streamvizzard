from typing import Optional, Dict

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(SignalType())
class Resample(Operator):
    def __init__(self, opID: int):
        super(Resample, self).__init__(opID, 1, 1)

        self.sampleRate = 0
        self.mode = 0

    def setData(self, data: Dict):
        self.sampleRate = data["sampleRate"]
        self.mode = data["mode"]

    def getData(self) -> dict:
        return {"sampleRate": self.sampleRate, "mode": self.mode}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        audioSignal: Signal = tupleIn.data[0]

        return self.createTuple((audioSignal.getResampled(self.sampleRate, self.mode),))
