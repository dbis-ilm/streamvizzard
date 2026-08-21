from typing import Optional, Dict

from scipy import signal

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(SignalType())
class NotchFilter(Operator):
    def __init__(self, opID: int):
        super(NotchFilter, self).__init__(opID, 1, 1)

        self.frequency = 0.0
        self.quality = 0

    def setData(self, data: Dict):
        self.frequency = data["frequency"]
        self.quality = data["quality"]

    def getData(self) -> dict:
        return {"frequency": self.frequency, "quality": self.quality}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        audioSignal: Signal = tupleIn.data[0]

        b, a = signal.iirnotch(self.frequency, self.quality, audioSignal.samplingRate)
        filteredData = signal.filtfilt(b, a, audioSignal.data, axis=0)

        return self.createTuple((Signal(audioSignal.samplingRate, filteredData),))
