from typing import Optional, Dict

import numpy as np

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(SignalType())
class ExtractChannels(Operator):
    def __init__(self, opID: int):
        super(ExtractChannels, self).__init__(opID, 1, 1)

        self.channelsRaw = ""  # Allows data such as individual channels and ranges: 1,2,4-6,9
        self._channelMask = []

    def setData(self, data: Dict):
        self.channelsRaw = data["channels"]

    def getData(self) -> dict:
        return {"channels": self.channelsRaw}

    def _updateChannelMask(self, channelCount: int):
        if len(self._channelMask) != channelCount:
            self._channelMask = np.zeros(channelCount, dtype=bool)

            # Assumes, channel idx start at 1
            for p in self.channelsRaw.split(","):
                p = p.strip()

                if len(p) == 0:
                    continue

                if "-" in p:  # Range selector
                    a, b = map(int, p.split("-"))
                    self._channelMask[a - 1:b] = True
                else:  # Specific channel
                    self._channelMask[int(p) - 1] = True

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        audioSignal: Signal = tupleIn.data[0]

        self._updateChannelMask(audioSignal.channels)

        channelData = audioSignal.data[:, self._channelMask]

        return self.createTuple((Signal(audioSignal.samplingRate, channelData),))
