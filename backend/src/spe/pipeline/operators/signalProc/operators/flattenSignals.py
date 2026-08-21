from typing import Optional, Dict

import numpy as np

from spe.common.dataType import ArrayType
from spe.pipeline.operators.operator import Operator
from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.common.tuple import Tuple


@Operator.requiresInput(ArrayType(entryType=SignalType()))
class FlattenSignals(Operator):
    def __init__(self, opID: int):
        super(FlattenSignals, self).__init__(opID, 1, 1)

    def setData(self, data: Dict):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        signalList = tupleIn.data[0]

        if len(signalList) == 0:
            return None

        firstSig = signalList[0]

        # Constraint: Sampling rate and channel count must be the same for an input signals!

        if any(s.samplingRate != firstSig.samplingRate or s.channels != firstSig.channels for s in signalList):
            self.onExecutionError("Signals have varying sampling rates or channels!")

            return None

        data = np.concatenate([s.data for s in signalList])

        return self.createTuple((Signal(firstSig.samplingRate, data),))
