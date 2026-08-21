from typing import Optional, Dict

from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class Cast(Operator):
    def __init__(self, opID: int):
        super(Cast, self).__init__(opID, 1, 1)

        self.mode = None

    def setData(self, data: Dict):
        self.mode = data["mode"]

    def getData(self) -> dict:
        return {"mode": self.mode}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        dataIn = tupleIn.data[0]

        dataOut = dataIn

        if self.mode == "bool":
            dataOut = bool(dataIn)
        elif self.mode == "int":
            dataOut = int(dataIn)
        elif self.mode == "float":
            dataOut = float(dataIn)
        elif self.mode == "string":
            dataOut = str(dataIn)

        return self.createTuple((dataOut,))
