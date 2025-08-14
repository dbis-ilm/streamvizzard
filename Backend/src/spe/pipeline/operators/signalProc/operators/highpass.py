import json
from typing import Optional

from scipy import signal

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class Highpass(Operator):
    def __init__(self, opID: int):
        super(Highpass, self).__init__(opID, 1, 1)

        self.threshold = 0.0
        self.order = 0

    def setData(self, data: json):
        self.threshold = data["threshold"]
        self.order = data["order"]

    def getData(self) -> dict:
        return {"threshold": self.threshold, "order": self.order}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        audioSignal = tupleIn.data[0]

        normal_cutoff = self.threshold / audioSignal.nyq()
        b, a = signal.butter(self.order, normal_cutoff, 'highpass')
        filteredData = signal.filtfilt(b, a, audioSignal.data)

        return self.createTuple((Signal(audioSignal.samplingRate, list(filteredData)),))
