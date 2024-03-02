import json
from typing import Optional

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class GaussianBlur(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(GaussianBlur, self).__init__(opID, 1, 1)

        self.kernelX = 0
        self.kernelY = 0

        self.sigmaX = 0
        self.sigmaY = 0

        self.sigmaXKernel = None
        self.sigmaYKernel = None

    def setData(self, data: json):
        self.kernelX = data["kernelX"]
        self.kernelY = data["kernelY"]
        self.sigmaX = data["sigmaX"]
        self.sigmaY = data["sigmaY"]

    def getData(self) -> dict:
        return {"kernelX": self.kernelX, "kernelY": self.kernelY, "sigmaX": self.sigmaX, "sigmaY": self.sigmaY}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        res = cv2.GaussianBlur(tupleIn.data[0].mat, (self.kernelX,
                               self.kernelY), self.sigmaX, self.sigmaY)

        return self.createTuple((Image(res),))
