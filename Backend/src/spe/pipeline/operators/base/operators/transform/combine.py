import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class Combine(Operator):
    """
    Inputs: Dynamic
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(Combine, self).__init__(opID, 1, 1)

        self.ins = 0

    def setData(self, data: json):
        self.ins = data["ins"]

        # Adjust IN sockets if required

        if len(self.inputs) != self.ins:
            self._configureSockets(self.ins, 1)

    def getData(self) -> dict:
        return {"ins": self.ins}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        # Single output -> combine all elements to a tuple

        return self.createTuple((tupleIn.data,))
