import json
from typing import Optional

import cv2
import numpy as np

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class Convert(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(Convert, self).__init__(opID, 1, 1)

        self.mode = 0
        self.modeRaw = None

    def setData(self, data: json):
        self.modeRaw = data["mode"]

        if self.modeRaw == "grayscale":
            self.mode = 0
        elif self.modeRaw == "bgr":
            self.mode = 1
        elif self.modeRaw == "float32":
            self.mode = 2

    def getData(self) -> dict:
        return {"mode": self.modeRaw}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        # TODO: CHECK IF CONVERSION IS EVEN POSSIBLE -> RETHINK IF THE CURRENT CONVERSIONS MAKE SENSE!

        res = tupleIn.data[0].mat
        if self.mode == 0:
            res = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        elif self.mode == 1:
            res = cv2.cvtColor(res, cv2.COLOR_GRAY2BGR)
        elif self.mode == 2:
            res = res.astype(np.float32)
        return self.createTuple((Image(res),))

