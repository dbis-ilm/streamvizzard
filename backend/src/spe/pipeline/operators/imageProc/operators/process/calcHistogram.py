from typing import Optional, Dict

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import ImageType, Image
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


@Operator.requiresInput(ImageType())
class CalcHistogram(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(CalcHistogram, self).__init__(opID, 1, 1)

    def setData(self, data: Dict):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img: Image = tupleIn.data[0]

        histoData = []
        for i in range(0, img.mat.shape[2] if len(img.mat.shape) > 2 else 1):
            # Calc Histo
            hist = cv2.calcHist([img.mat], [i], None, [256], [0, 256]).flatten().tolist()
            histoData.append(hist)

        return self.createTuple((histoData,))
