import json
import statistics as stat
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class Inconsistency(Operator):
    def __init__(self, opID: int):
        super(Inconsistency, self).__init__(opID, 1, 2)

        self.mode = None

        self.threshold = 0
        self.maxValue = 0

    def setData(self, data: json):
        self.threshold = int(data["threshold"])
        self.maxValue = int(data["maxValue"])
        self.mode = data["mode"]  # [mean, median]

    def getData(self) -> dict:
        return {"threshold": self.threshold, "maxValue": self.maxValue, "mode": self.mode}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        data = tupleIn.data[0]
        invalid = []

        for idx, item in enumerate(data):
            if item < self.threshold or item > self.maxValue:
                invalid.append(data[idx])

                if self.mode == "mode":
                    data[idx] = stat.mode(data)
                elif self.mode == "mean":
                    data[idx] = stat.mean(data)
                elif self.mode == "median":
                    data[idx] = stat.median(data)
                else:
                    del data[idx]
            else:
                invalid.append(None)

        return self.createTuple((data, invalid))
