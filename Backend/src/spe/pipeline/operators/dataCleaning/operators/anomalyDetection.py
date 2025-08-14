import json
import statistics as stat
from typing import Optional

import numpy as ny

from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from utils.utils import tryParseInt, clamp


class AnomalyDetection(Operator):
    def __init__(self, opID: int):
        super(AnomalyDetection, self).__init__(opID, 1, 2)

        self.mode = None
        self.upperQuantile = 75
        self.lowerQuantile = 25
        self.windowSize = 10

    def setData(self, data: json):
        self.mode = data["mode"]  # [mean, mode, median, remove]
        self.upperQuantile = clamp(tryParseInt(data["upperQuantile"], 75), 0, 100)
        self.lowerQuantile = clamp(tryParseInt(data["lowerQuantile"], 25), 0, 100)
        self.windowSize = tryParseInt(data["windowSize"], 10)

    def getData(self) -> dict:
        return {"mode": self.mode, "upperQuantile": self.upperQuantile, "lowerQuantile": self.lowerQuantile, "windowSize": self.windowSize}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        data = tupleIn.data[0]

        Q3, Q1 = ny.percentile(data, [self.upperQuantile, self.lowerQuantile])
        IQR = Q3 - Q1

        # Finding the thresholds

        lower_limit = Q1 - 1.5 * IQR  # Lower threshold
        upper_limit = Q3 + 1.5 * IQR  # Higher threshold

        data_cleaned = []
        data_outlier = []

        fallbackVal = stat.median(data)

        for i, value in enumerate(data):
            if value < lower_limit or value > upper_limit:
                data_outlier.append(value)

                # Get surrounding values (excluding the current index)
                start = max(0, i - self.windowSize)
                end = min(len(data), i + self.windowSize + 1)
                neighbors = [data[j] for j in range(start, end) if j != i]

                # Determine replacement based on mode
                if neighbors:
                    if self.mode == "mean":
                        replacement = stat.mean(neighbors)
                    elif self.mode == "median":
                        replacement = stat.median(neighbors)
                    elif self.mode == "mode":
                        try:
                            replacement = stat.mode(neighbors)
                        except stat.StatisticsError:
                            replacement = fallbackVal
                    else:
                        replacement = fallbackVal
                else:
                    replacement = fallbackVal

                data_cleaned.append(replacement)
            else:
                data_outlier.append(None)
                data_cleaned.append(value)

        return self.createTuple((data_cleaned, data_outlier))
