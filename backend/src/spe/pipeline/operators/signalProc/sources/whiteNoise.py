import time
from typing import Dict

import numpy as np

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal
from spe.pipeline.operators.source import Source


class WhiteNoise(Source):
    def __init__(self,  opID: int):
        super(WhiteNoise, self).__init__(opID, 0, 1)

        self.samplingRate = 0
        self.chunkSize = 0
        self.channels = 0

    def getData(self) -> dict:
        return {"samplingRate": self.samplingRate, "channels": self.channels, "chunkSize": self.chunkSize}

    def setData(self, data: Dict):
        self.samplingRate = data["samplingRate"]
        self.channels = data["channels"]
        self.chunkSize = data["chunkSize"]

    def _runSource(self):
        while self.isRunning():
            sig = np.random.uniform(-1.0, 1.0, (self.chunkSize, self.channels))

            self._produce((Signal(self.samplingRate, sig),))

            sleepDuration = self.chunkSize / self.samplingRate

            if sleepDuration > 1e-3:
                time.sleep(sleepDuration)
