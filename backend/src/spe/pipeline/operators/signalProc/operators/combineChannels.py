from typing import Optional, Dict

import numpy as np

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(SignalType())
class CombineChannels(Operator):
    def __init__(self, opID: int):
        super(CombineChannels, self).__init__(opID, 1, 1)

        self.ins = 0

    def setData(self, data: Dict):
        self.ins = data["ins"]

        # Adjust IN sockets if required

        if len(self.inputs) != self.ins:
            self._configureSockets(self.ins, 1)

    def getData(self) -> dict:
        return {"ins": self.ins}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        signalList = tupleIn.data

        if len(signalList) == 0:
            return None

        firstSig = signalList[0]

        # Constraint: Sampling rate and sample count must be the same for all signals!

        if any(firstSig.samplingRate != s.samplingRate or firstSig.samples != s.samples for s in signalList):
            self.onExecutionError("Sampling rate or sample count not matching!")

            return None

        # Combines all channels into one output signal
        mergedData = np.concatenate([s.data for s in signalList], axis=1)

        return self.createTuple((Signal(firstSig.samplingRate, mergedData),))
