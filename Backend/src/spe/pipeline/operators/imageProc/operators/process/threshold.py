import json
from typing import Optional

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class Threshold(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(Threshold, self).__init__(opID, 1, 1)

        self.threshold = 0
        self.maxValue = 0

        self.modeRaw = 0
        self.mode = 0

    def setData(self, data: json):
        self.threshold = int(data["threshold"])
        self.maxValue = int(data["maxVal"])

        self.modeRaw = data["mode"]

        if self.modeRaw == "binary":
            self.mode = cv2.THRESH_BINARY
        elif self.modeRaw == "binaryInv":
            self.mode = cv2.THRESH_BINARY_INV
        elif self.modeRaw == "trunc":
            self.mode = cv2.THRESH_TRUNC
        elif self.modeRaw == "zero":
            self.mode = cv2.THRESH_TOZERO
        else:
            self.mode = cv2.THRESH_TOZERO_INV

    def getData(self) -> dict:
        return {"threshold": self.threshold, "maxVal": self.maxValue, "mode": self.modeRaw}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        if not tupleIn.data[0].isGrey():
            return None

        _, res = cv2.threshold(
            tupleIn.data[0].mat, self.threshold, self.maxValue, self.mode)

        return self.createTuple((Image(res),))
