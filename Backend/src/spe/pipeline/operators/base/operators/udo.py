import json
from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.tuple import Tuple
from utils.utils import instantiateUserDefinedClass


class UDO(Operator):
    def __init__(self,  opID: int):
        super(UDO, self).__init__(opID, 1, 1)

        self.code = None
        self._instance = None

    def setData(self, data: json):
        socksIn = data["inputs"]
        socksOut = data["outputs"]

        self._configureSockets(socksIn, socksOut)

        if self.code != data["code"]:
            self.code = data["code"]

            self._instance = instantiateUserDefinedClass(self, self.code, self._instance)

    def getData(self) -> dict:
        return {"code": self.code, "inputs": len(self.inputs), "outputs": len(self.outputs)}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        if self._instance is not None:
            try:
                res = self._instance.execute(tupleIn)

                if res is not None:
                    return self.createTuple(res)
            except Exception:
                self.onExecutionError()

        return None

    def onRuntimeDestroy(self):
        super(UDO, self).onRuntimeDestroy()

        if self._instance is not None:
            self._instance.onDestroy()
