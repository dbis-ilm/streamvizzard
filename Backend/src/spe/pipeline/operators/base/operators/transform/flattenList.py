import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class FlattenList(Operator):
    def __init__(self, opID: int):
        super(FlattenList, self).__init__(opID, 1, 1)

    def setData(self, data: json):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        data = tupleIn.data[0]

        return self.createTuple(([x for xs in data for x in xs],))
