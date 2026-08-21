from typing import Optional, Dict

import cv2
import numpy as np

from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from utils.utils import tryParseFloat


@Operator.requiresInput(ImageType())
class ImgMultiply(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(ImgMultiply, self).__init__(opID, 1, 1)

        self.value: np.ndarray = np.array(0)
        self.rawValue = 0

    def setData(self, data: Dict):
        self.rawValue = tryParseFloat(data["value"], 0)
        self.value = np.array([self.rawValue] * 4)  # Scalar is a tuple of 4 values

    def getData(self) -> dict:
        return {"value": self.rawValue}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img: Image = tupleIn.data[0]

        res = cv2.multiply(img.mat, self.value)

        return self.createTuple((Image(res),))
