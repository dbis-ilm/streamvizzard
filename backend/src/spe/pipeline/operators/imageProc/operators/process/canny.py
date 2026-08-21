from typing import Optional, Dict

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from utils.utils import tryParseFloat, tryParseInt


@Operator.requiresInput(ImageType())
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

    def setData(self, data: Dict):
        self.threshold1 = tryParseFloat(data["threshold1"])
        self.threshold2 = tryParseFloat(data["threshold2"])
        self.aperture = tryParseInt(data["aperture"])

    def getData(self) -> dict:
        return {"threshold1": self.threshold1, "threshold2": self.threshold2, "aperture": self.aperture}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img: Image = tupleIn.data[0]

        res = cv2.Canny(img.mat, self.threshold1, self.threshold2, apertureSize=self.aperture)

        return self.createTuple((Image(res),))
