from typing import Optional, Dict

from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from utils.utils import tryParseInt


@Operator.requiresInput(ImageType())
class ExtractROI(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(ExtractROI, self).__init__(opID, 1, 1)

        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

    def setData(self, data: Dict):
        self.x = tryParseInt(data["x"])
        self.y = tryParseInt(data["y"])
        self.w = tryParseInt(data["w"])
        self.h = tryParseInt(data["h"])

    def getData(self) -> dict:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        img: Image = tupleIn.data[0]

        return self.createTuple((Image(img.mat[self.y:self.y+self.h, self.x:self.x+self.w].copy()),))
