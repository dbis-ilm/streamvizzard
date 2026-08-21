from typing import Optional, Dict

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from utils.utils import tryParseFloat, tryParseInt


@Operator.requiresInput(ImageType())
class GaussianBlur(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(GaussianBlur, self).__init__(opID, 1, 1)

        self.kernelX = 0
        self.kernelY = 0

        self.sigmaX = 0.0
        self.sigmaY = 0.0

        self.sigmaXKernel = None
        self.sigmaYKernel = None

    def setData(self, data: Dict):
        self.kernelX = tryParseInt(data["kernelX"])
        self.kernelY = tryParseInt(data["kernelY"])
        self.sigmaX = tryParseFloat(data["sigmaX"])
        self.sigmaY = tryParseFloat(data["sigmaY"])

    def getData(self) -> dict:
        return {"kernelX": self.kernelX, "kernelY": self.kernelY, "sigmaX": self.sigmaX, "sigmaY": self.sigmaY}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img: Image = tupleIn.data[0]

        res = cv2.GaussianBlur(img.mat, [self.kernelX, self.kernelY], self.sigmaX, None, self.sigmaY)

        return self.createTuple((Image(res),))
