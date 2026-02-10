import json
from typing import Optional

import cv2

from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class CalcHistogram(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(CalcHistogram, self).__init__(opID, 1, 1)

    def setData(self, data: json):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        mat = tupleIn.data[0].mat

        histoData = []
        for i in range(0, mat.shape[2] if len(mat.shape) > 2 else 1):
            # Calc Histo
            hist = cv2.calcHist([mat], [i], None, [256], [0, 256]).flatten().tolist()
            histoData.append(hist)

        return self.createTuple((histoData,))
