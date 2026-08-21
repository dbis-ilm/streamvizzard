from typing import Optional, Dict

from scipy import signal

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(SignalType())
class Lowpass(Operator):
    def __init__(self, opID: int):
        super(Lowpass, self).__init__(opID, 1, 1)

        self.threshold = 0.0
        self.order = 0

    def setData(self, data: Dict):
        self.threshold = data["threshold"]
        self.order = data["order"]

    def getData(self) -> dict:
        return {"threshold": self.threshold, "order": self.order}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        audioSignal = tupleIn.data[0]

        normalCutoff = self.threshold / audioSignal.nyq()
        sos = signal.butter(self.order, normalCutoff, btype='lowpass', output='sos')
        filteredData = signal.sosfiltfilt(sos, audioSignal.data, axis=0)

        return self.createTuple((Signal(audioSignal.samplingRate, filteredData),))
