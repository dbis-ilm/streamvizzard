import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple
from utils.utils import createUDFFunction


class UDF(Operator):
    def __init__(self, opID: int):
        super(UDF, self).__init__(opID, 0, 0)

        self.rawCode = ""
        self.code = ""
        self.persistent = None

    def setData(self, data: json):
        self.rawCode = data["code"]
        self.code = createUDFFunction(self.rawCode, True)

        socksIn = data["inputs"]
        socksOut = data["outputs"]

        self._configureSockets(socksIn, socksOut)

    def getData(self) -> dict:
        return {"code": self.rawCode, "inputs": len(self.inputs), "outputs": len(self.outputs)}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        # CARE: exec IS A HUGE SECURITY RISK!

        loc = {"data": tupleIn.data, "tuple": tupleIn, "res": None, "persistent": self.persistent}
        exec(self.code, globals(), loc)

        res = loc["res"]
        self.persistent = loc["persistent"]

        if isinstance(res, tuple):
            return self.createTuple(res)

        return None
