import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class Combine(Operator):
    """
    Inputs: Dynamic
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(Combine, self).__init__(opID, 1, 1)

        self.ins = 0
        self.outs = 0

    def setData(self, data: json):
        self.ins = data["ins"]
        self.outs = data["outs"]

        # Adjust IN sockets if required

        if len(self.inputs) != self.ins or len(self.outputs) != self.outs:
            self._configureSockets(self.ins, self.outs)

    def getData(self) -> dict:
        return {"ins": self.ins, "outs": self.outs}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        # Single output -> combine all elements to a tuple

        if len(self.outputs) == 1:
            return self.createTuple((tupleIn.data,))

        # Else distribute elements to out sockets

        return self.createTuple(tupleIn.data)
