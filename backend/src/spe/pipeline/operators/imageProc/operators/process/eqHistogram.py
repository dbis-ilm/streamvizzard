from typing import Optional, Dict

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(ImageType())
class EqHistogram(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(EqHistogram, self).__init__(opID, 1, 1)

    def setData(self, data: Dict):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img: Image = tupleIn.data[0]

        res = cv2.equalizeHist(img.mat)

        return self.createTuple((Image(res),))
