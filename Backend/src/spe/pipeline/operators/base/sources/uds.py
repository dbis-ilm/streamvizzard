import json

from spe.pipeline.operators.source import Source
from utils.utils import instantiateUserDefinedClass


class UDS(Source):
    def __init__(self,  opID: int):
        super(UDS, self).__init__(opID, 0, 1)

        self.code = None
        self._instance = None

    def setData(self, data: json):
        socksOut = data["outputs"]

        self._configureSockets(0, socksOut)

        if self.code != data["code"]:
            self.code = data["code"]

            self._instance = instantiateUserDefinedClass(self, self.code, self._instance)

    def getData(self) -> dict:
        return {"outputs": len(self.outputs), "code": self.code}

    def _runSource(self):
        while self.isRunning():
            if self._instance is None:
                continue

            try:
                tup = self._instance.runLoop()  # Call of runFunction
                if tup is not None:
                    self._produce(tup)
            except Exception:
                self.onExecutionError()

        if self._instance is not None:
            self._instance.onDestroy()

    def onRuntimeDestroy(self):
        super(UDS, self).onRuntimeDestroy()

        if self._instance is not None:
            self._instance.onDestroy()
