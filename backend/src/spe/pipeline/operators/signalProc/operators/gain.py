from typing import Optional, Dict

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from utils.utils import tryParseFloat


@Operator.requiresInput(SignalType())
class Gain(Operator):
    def __init__(self, opID: int):
        super(Gain, self).__init__(opID, 1, 1)

        self.gain = 0

    def setData(self, data: Dict):
        self.gain = tryParseFloat(data["gain"], 1)

    def getData(self) -> dict:
        return {"gain": self.gain}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        audioSignal: Signal = tupleIn.data[0]

        audioSignal.data = audioSignal.data * self.gain

        return self.createTuple((audioSignal,))
