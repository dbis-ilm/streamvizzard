import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class ToFloat(Operator):
    def __init__(self, opID: int):
        super(ToFloat, self).__init__(opID, 1, 1)

    def setData(self, data: json):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        return self.createTuple((float(tupleIn.data[0]),))
