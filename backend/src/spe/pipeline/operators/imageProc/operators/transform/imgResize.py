from typing import Optional, Dict

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(ImageType())
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

    def setData(self, data: Dict):
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
        img: Image = tupleIn.data[0]

        width = int(self.scaleX if self.useAbsoluteScaleX else img.mat.shape[1] * self.scaleX / 100)
        height = int(self.scaleY if self.useAbsoluteScaleY else img.mat.shape[0] * self.scaleY / 100)

        res = cv2.resize(img.mat, (width, height))

        return self.createTuple((Image(res),))
