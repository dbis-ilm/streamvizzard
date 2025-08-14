from typing import Type, List, Optional

from spe.pipeline.operators.operator import Operator
from spe.pipeline.socket import Socket


class AdvisorSuggestion:
    def __init__(self, operators: List[Type[Operator]], socket: Optional[Socket], msg: str = None):
        self._operators = operators
        self._socket = socket
        self._msg = msg

    def getData(self) -> dict:
        from spe.pipeline.operators.operatorDB import getPathByOperator

        res = {"msg": self._msg,
               "socket": {"in": self._socket.inSocket, "id": self._socket.id} if self._socket is not None else None}

        ops = []

        for op in self._operators:
            opData = {"name": op.__name__, "path": getPathByOperator(op)}
            ops.append(opData)

        res["ops"] = ops

        return res
