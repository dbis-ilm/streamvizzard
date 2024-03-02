import json
from typing import Optional

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


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

    def setData(self, data: json):
        self.x = data["x"]
        self.y = data["y"]
        self.w = data["w"]
        self.h = data["h"]

    def getData(self) -> dict:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        return self.createTuple((Image(tupleIn.data[0].mat[self.y:self.y+self.h, self.x:self.x+self.w]),))
