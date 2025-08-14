import json
from typing import Optional

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class ImgResize(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(ImgResize, self).__init__(opID, 1, 1)

        self.scaleXRaw = None
        self.scaleYRaw = None

        self.scaleX = 0
        self.scaleY = 0

        self.useAbsoluteScaleX = True
        self.useAbsoluteScaleY = True

    def setData(self, data: json):
        self.scaleXRaw = data["scaleX"]
        self.scaleYRaw = data["scaleY"]

        rawX = self.scaleXRaw
        rawY = self.scaleYRaw

        if str(rawX).endswith("%"):
            rawX = rawX.replace("%", "")
            self.useAbsoluteScaleX = False
        else:
            self.useAbsoluteScaleX = True

        self.scaleX = int(float(rawX))

        if str(self.scaleYRaw).endswith("%"):
            rawY = self.scaleYRaw.replace("%", "")
            self.useAbsoluteScaleY = False
        else:
            self.useAbsoluteScaleY = True

        self.scaleY = int(float(rawY))

    def getData(self) -> dict:
        return {"scaleX": self.scaleXRaw, "scaleY": self.scaleYRaw}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img = tupleIn.data[0].mat

        width = int(self.scaleX if self.useAbsoluteScaleX else img.shape[1] * self.scaleX / 100)
        height = int(self.scaleY if self.useAbsoluteScaleY else img.shape[0] * self.scaleY / 100)

        img = cv2.resize(img, (width, height))

        return self.createTuple((Image(img),))
