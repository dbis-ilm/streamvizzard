from typing import Dict, Optional, List

import numpy as np

from spe.common.timer import Timer


class HeatmapD(dict):
    def __init__(self, x: List, y: List, z: List[List], settings: Dict):
        self.time = Timer.currentTime()
        self.x = x
        self.y = y
        self.z = z

        self._downsample(settings.get("maxCells", None))

        # To allow JSON serialization
        dict.__init__(self, x=self.x, y=self.y, z=self.z, time=self.time)

    def _downsample(self, maxCells: Optional[int]):
        if maxCells is None:
            return

        z = np.asarray(self.z)

        xCount = len(self.z[0])
        yCount = len(self.z)

        cells = yCount * xCount

        if cells <= maxCells:
            return

        scale = np.sqrt(maxCells / cells)

        newY = max(1, int(yCount * scale))
        newX = max(1, int(xCount * scale))

        yIdx = np.linspace(0, yCount - 1, newY, dtype=np.int32)
        xIdx = np.linspace(0, xCount - 1, newX, dtype=np.int32)

        self.x = [self.x[i] for i in xIdx]
        self.y = [self.y[i] for i in yIdx]
        self.z = z[np.ix_(yIdx, xIdx)].tolist()
