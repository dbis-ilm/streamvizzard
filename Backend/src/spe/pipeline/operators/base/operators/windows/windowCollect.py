import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class WindowCollect(Operator):
    def __init__(self, opID: int):
        super(WindowCollect, self).__init__(opID, 1, 1)

    def setData(self, data: json):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        window = tupleIn.data[0]

        return self.createTuple((window.toDataArray(),))
