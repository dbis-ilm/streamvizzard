from typing import Optional, Dict

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from utils.utils import tryParseFloat


@Operator.requiresInput(ImageType())
class ImgBlend(Operator):
    """
    Inputs: 2
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(ImgBlend, self).__init__(opID, 2, 1)

        self.alpha = 0

    def setData(self, data: Dict):
        self.alpha = tryParseFloat(data["alpha"])

    def getData(self) -> dict:
        return {"alpha": self.alpha}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img1: Image = tupleIn.data[0]
        img2: Image = tupleIn.data[1]

        res = cv2.addWeighted(img1.mat, self.alpha, img2.mat, 1 - self.alpha, 0)

        return self.createTuple((Image(res),))
