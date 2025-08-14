import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class ToInt(Operator):
    def __init__(self, opID: int):
        super(ToInt, self).__init__(opID, 1, 1)

    def setData(self, data: json):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        return self.createTuple((int(float(tupleIn.data[0])),))
