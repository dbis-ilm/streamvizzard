import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple
from utils.utils import createUDFFunction


class Filter(Operator):
    def __init__(self, opID: int):
        super(Filter, self).__init__(opID, 1, 1)

        self.rawCode = ""
        self.code = ""
        self.persistent = None

    def setData(self, data: json):
        self.rawCode = data["code"]
        self.code = createUDFFunction(self.rawCode, True)

    def getData(self) -> dict:
        return {"code": self.rawCode}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        # CARE: exec IS A HUGE SECURITY RISK!

        loc = {"data": tupleIn.data, "tuple": tupleIn, "res": None, "persistent": self.persistent}
        exec(self.code, globals(), loc)

        res = loc["res"]
        self.persistent = loc["persistent"]

        if res is None or not res:
            return None

        return self.createTuple(tupleIn.data)
