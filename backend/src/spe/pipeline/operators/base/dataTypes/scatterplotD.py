from typing import Dict, List, Optional

from spe.common.timer import Timer
from utils.utils import tryParseInt


class ScatterplotD(dict):
    def __init__(self, plots: List[List], settings: Dict):
        # This might contain multiple plots [ [], [] ]
        # Each plot contains of an array of elements (one-axis (y) or two-axis (x,y))

        self.time = Timer.currentTime()
        self.plots = [self._prepareData(d, settings) for d in plots]

        # To allow JSON serialization
        dict.__init__(self, plots=self.plots, time=self.time)

    @staticmethod
    def fromElement(element, settings: Dict):
        plots = [[element]]

        return ScatterplotD(plots, settings)

    @staticmethod
    def fromElements(elements: List, settings: Dict):
        plots = [elements]

        return ScatterplotD(plots, settings)

    @staticmethod
    def _prepareData(data: List, settings: Dict):
        mp: Optional[int] = tryParseInt(settings.get("maxBufferElements"), -1)

        if mp == -1:  # Unlimited
            return data

        n = len(data)

        if n == 0 or mp <= 0:
            return []
        if n == 1 or mp == 1:
            return [data[0]]
        if mp >= n:
            return data

        step = n - 1
        div = mp - 1

        resData: List = [0] * mp

        for i in range(mp):
            dataIdx = (i * step) // div
            resData[i] = data[dataIdx]

        return resData
