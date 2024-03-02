import json
from typing import Optional

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class Canny(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(Canny, self).__init__(opID, 1, 1)

        self.threshold1 = 0
        self.threshold2 = 0
        self.aperture = 0

    def setData(self, data: json):
        self.threshold1 = data["threshold1"]
        self.threshold2 = data["threshold2"]
        self.aperture = data["aperture"]

    def getData(self) -> dict:
        return {"threshold1": self.threshold1, "threshold2": self.threshold2, "aperture": self.aperture}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        res = cv2.Canny(tupleIn.data[0].mat, self.threshold1, self.threshold2, apertureSize=self.aperture)

        return self.createTuple((Image(res),))
