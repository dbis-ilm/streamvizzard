import json
from typing import Optional

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class ImgBlend(Operator):
    """
    Inputs: 2
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(ImgBlend, self).__init__(opID, 2, 1)

        self.alpha = 0

    def setData(self, data: json):
        self.alpha = data["alpha"]

    def getData(self) -> dict:
        return {"alpha": self.alpha}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        res = cv2.addWeighted(tupleIn.data[0].mat, self.alpha,
                              tupleIn.data[1].mat, 1 - self.alpha, 0)

        return self.createTuple((Image(res),))
