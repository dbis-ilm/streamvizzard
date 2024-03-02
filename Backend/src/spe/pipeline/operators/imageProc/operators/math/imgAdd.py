import json
from typing import Optional

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class ImgAdd(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(ImgAdd, self).__init__(opID, 1, 1)

        self.value = 0
        self.rawValue = 0

    def setData(self, data: json):
        self.rawValue = data["value"]
        self.value = tuple([self.rawValue] * 4)  # Scalar is a tuple of 4 values

    def getData(self) -> dict:
        return {"value": self.rawValue}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        mat = tupleIn.data[0].mat

        res = cv2.add(mat, self.value)

        return self.createTuple((Image(res),))
