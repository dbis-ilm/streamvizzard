import json
from typing import Optional

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class ImgLoad(Operator):
    def __init__(self, opID: int):
        super(ImgLoad, self).__init__(opID, 1, 1)

        self.flags = 0

    def setData(self, data: json):
        if data["flags"] != "":
            try:
                self.flags = int(data["flags"])
            except Exception:
                self.onExecutionError()

                self.flags = None
        else:
            self.flags = None

    def getData(self) -> dict:
        return {"flags": self.flags}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        path = tupleIn.data[0]

        if self.flags is not None:
            img = cv2.imread(path, self.flags)
        else:
            img = cv2.imread(path)

        return self.createTuple((Image(img),))
