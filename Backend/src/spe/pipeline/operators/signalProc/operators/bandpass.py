import json
from typing import Optional

from scipy import signal

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class Bandpass(Operator):
    def __init__(self, opID: int):
        super(Bandpass, self).__init__(opID, 1, 1)

        self.threshold1 = 0.0
        self.threshold2 = 0.0
        self.order = 0

    def setData(self, data: json):
        self.threshold1 = data["threshold1"]
        self.threshold2 = data["threshold2"]
        self.order = data["order"]

    def getData(self) -> dict:
        return {"threshold1": self.threshold1, "threshold2": self.threshold2, "order": self.order}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        audioSignal = tupleIn.data[0]

        normal_cutoff1 = self.threshold1 / audioSignal.nyq()
        normal_cutoff2 = self.threshold2 / audioSignal.nyq()

        b, a = signal.butter(self.order, [normal_cutoff1, normal_cutoff2], 'band')
        filteredData = signal.filtfilt(b, a, audioSignal.data)

        return self.createTuple((Signal(audioSignal.samplingRate, list(filteredData)),))
