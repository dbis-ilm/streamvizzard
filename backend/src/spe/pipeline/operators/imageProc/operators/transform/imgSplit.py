import json
from typing import Optional

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class ImgSplit(Operator):
    """
    Inputs: 1
    Outputs: 4
    """

    def __init__(self, opID: int):
        super(ImgSplit, self).__init__(opID, 1, 4)

    def setData(self, data: json):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        inMat = tupleIn.data[0].mat

        resCh = cv2.split(inMat)  # Tuple of Mats

        imgArray = [None] * len(self.outputs)

        for i in range(0, min(len(self.outputs), len(resCh))):
            mt = resCh[i]

            # Fill all other channels with zero and place the extracted channel
            # res = np.zeros(inMat.shape)
            # res[:, :, i] = mt

            imgArray[i] = Image(mt)

        return self.createTuple(tuple(imgArray))
