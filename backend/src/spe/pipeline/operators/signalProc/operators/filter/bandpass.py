from typing import Optional, Dict

from scipy import signal

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(SignalType())
class Bandpass(Operator):
    def __init__(self, opID: int):
        super(Bandpass, self).__init__(opID, 1, 1)

        self.threshold1 = 0.0
        self.threshold2 = 0.0
        self.order = 0

    def setData(self, data: Dict):
        self.threshold1 = data["threshold1"]
        self.threshold2 = max(self.threshold1 + 1, data["threshold2"])
        self.order = data["order"]

    def getData(self) -> dict:
        return {"threshold1": self.threshold1, "threshold2": self.threshold2, "order": self.order}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        audioSignal = tupleIn.data[0]

        normalCutoff1 = self.threshold1 / audioSignal.nyq()
        normalCutoff2 = self.threshold2 / audioSignal.nyq()

        sos = signal.butter(self.order, [normalCutoff1, normalCutoff2], btype='band', output='sos')
        filteredData = signal.sosfiltfilt(sos, audioSignal.data, axis=0)

        return self.createTuple((Signal(audioSignal.samplingRate, filteredData),))
