import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple


class StringSplit(Operator):
    """
    Inputs: 1
    Outputs: Dynamic based on split
    """

    def __init__(self, opID: int):
        super(StringSplit, self).__init__(opID, 1, 1)

        self.delimiter = ","
        self.mode = 0  # 0: Split to output tuple, 1: Split to tuple as single output
        self.outs = 1

    def setData(self, data: json):
        self.mode = data["mode"]
        self.delimiter = data["delimiter"]
        self.outs = data["outs"]

        # Adjust OUT sockets if required

        if self.mode == 0:
            if len(self.outputs) != self.outs:
                self._configureSockets(1, self.outs)
        else:
            if len(self.outputs) != 1:
                self._configureSockets(1, 1)

    def getData(self) -> dict:
        return {"delimiter": self.delimiter, "mode": self.mode, "outs": self.outs}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        data = tupleIn.data[0]

        split = data.split(self.delimiter)

        if self.mode == 0:
            return self.createTuple(tuple(split))  # each element as separate output
        else:
            return self.createTuple((split,))  # array
