from typing import Optional, Dict

import cv2
import numpy as np
from numpy import uint8

from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from utils.utils import tryParseInt, tryParseFloat


@Operator.requiresInput(ImageType())
class FindContours(Operator):
    """
    Inputs: 1
    Outputs: 3
    """

    def __init__(self, opID: int):
        super(FindContours, self).__init__(opID, 1, 3)

        self.modeRaw = 0
        self.methodRaw = 0

        self.mode = 0
        self.method = 0

        self.drawContourThickness = 1

    def setData(self, data: Dict):
        self.drawContourThickness = tryParseFloat(data["drawThickness"], 0)
        self.modeRaw = tryParseInt(data["mode"])

        if self.modeRaw == 0:
            self.mode = cv2.RETR_LIST
        elif self.modeRaw == 1:
            self.mode = cv2.RETR_TREE
        elif self.modeRaw == 2:
            self.mode = cv2.RETR_CCOMP
        elif self.modeRaw == 3:
            self.mode = cv2.RETR_EXTERNAL
        elif self.modeRaw == 4:
            self.mode = cv2.RETR_FLOODFILL

        self.methodRaw = tryParseInt(data["method"])

        if self.methodRaw == 0:
            self.method = cv2.CHAIN_APPROX_NONE
        elif self.methodRaw == 1:
            self.method = cv2.CHAIN_APPROX_SIMPLE
        elif self.methodRaw == 2:
            self.method = cv2.CHAIN_APPROX_TC89_L1
        elif self.methodRaw == 3:
            self.method = cv2.CHAIN_APPROX_TC89_KCOS

    def getData(self) -> dict:
        return {"method": self.methodRaw, "mode": self.modeRaw, "drawThickness": self.drawContourThickness}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img: Image = tupleIn.data[0]

        contours, hierarchy = cv2.findContours(img.mat, self.mode, self.method)

        mat = np.zeros(img.mat.shape, dtype=uint8)
        cv2.drawContours(image=mat, contours=contours,
                         contourIdx=-1, thickness=self.drawContourThickness,
                         color=(255, 255, 255))

        return self.createTuple((Image(mat), contours, hierarchy))
