from typing import Optional, Dict, List

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(ImageType())
class ImgSplit(Operator):
    """
    Inputs: 1
    Outputs: 4
    """

    def __init__(self, opID: int):
        super(ImgSplit, self).__init__(opID, 1, 4)

    def setData(self, data: Dict):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img: Image = tupleIn.data[0]

        resCh = cv2.split(img.mat)  # Tuple of Mats

        imgArray: List[Optional[Image]] = [None] * len(self.outputs)

        for i in range(0, min(len(self.outputs), len(resCh))):
            mt = resCh[i]

            imgArray[i] = Image(mt)

        return self.createTuple(tuple(imgArray))
