from abc import ABC, abstractmethod
from typing import Type, List, Optional, Dict, Any

from spe.pipeline.operators.operator import Operator
from spe.pipeline.socket import Socket
from spe.pipeline.operators.operatorDB import getPathByOperator


class AdvisorSuggestion(ABC):
    def __init__(self, msg: str = None):
        self._msg = msg

    @abstractmethod
    def getData(self) -> Dict:
        pass


class AddOpAS(AdvisorSuggestion):
    class OpConfig:
        def __init__(self, opType: Type[Operator], params: Optional[Dict[str, Any]] = None):
            self.opType = opType
            self.params = params

    def __init__(self, operators: List[OpConfig], socket: Optional[Socket], msg: str = None):
        super().__init__(msg)

        self._operators = operators
        self._socket = socket

    def getData(self) -> dict:

        res = {"type": "AddOp", "msg": self._msg,
               "socket": {"in": self._socket.inSocket, "id": self._socket.id} if self._socket is not None else None}

        ops = []

        for op in self._operators:
            opData = {"name": op.opType.__name__, "path": getPathByOperator(op.opType), "params": op.params}
            ops.append(opData)

        res["ops"] = ops

        return res


class AdjustParamAS(AdvisorSuggestion):
    def __init__(self, params: Dict[str, Any], msg: str = None):
        """ params expects a dictionary of key:value tuples for the desired params to set. """

        super().__init__(msg)

        self.params = params

    def getData(self) -> dict:
        return {"type": "AdjParam", "msg": self._msg, "params": self.params}
