import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from utils.utils import escapeStr


class StringSplit(Operator):
    def __init__(self, opID: int):
        super(StringSplit, self).__init__(opID, 1, 1)

        self.delimiter = ","

    def setData(self, data: json):
        self.delimiter = escapeStr(data["delimiter"], True)

    def getData(self) -> dict:
        return {"delimiter": escapeStr(self.delimiter, False)}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        data = tupleIn.data[0]

        split = data.split(self.delimiter)

        return self.createTuple((split,))
