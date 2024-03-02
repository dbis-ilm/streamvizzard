import json
from typing import Optional, List

from spe.pipeline.operators.base.dataTypes.window import Window
from spe.pipeline.operators.operator import Operator
from spe.runtime.debugger.debuggingUtils import retrieveStoredDTRef
from spe.runtime.structures.tuple import Tuple


class TumblingWindowCount(Operator):
    def __init__(self, opID: int):
        super(TumblingWindowCount, self).__init__(opID, 1, 1, pipelineBreaker=True)

        self.value = 0

        self.buffer: List[Tuple] = list()

    def setData(self, data: json):
        self.value = float(data["value"])

    def getData(self) -> dict:
        return {"value": self.value}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self.buffer.append(tupleIn)

        if self.isDebuggingEnabled():
            self._onDebugEx(tupleIn)

        if len(self.buffer) >= self.value:
            r = Window(self.buffer.copy())
            self.buffer.clear()

            tup = self.createTuple((r,))

            return tup

        return None

    # ----------------------------- DEBUGGING -----------------------------
    def _onDebugEx(self, tupleIn: Tuple):
        if len(self.buffer) < self.value:  # Only store tuple if it does not complete the buffer
            self._getExecuteDT().registerAttribute("opEx_addedTup", tupleIn.uuid)

    def _onExecutionUndo(self, tup: Tuple):
        addedTup = self.getDebugger().getDT(tup).getAttribute("opEx_addedTup")

        if addedTup is None:  # The undone tuple completed the buffer, restore buffer from result tuple
            winData: Window = tup.data[0]
            self.buffer = winData.getTuples().copy()

        self.buffer.pop()

    def _onExecutionRedo(self, tup: Tuple):
        addedTup = self.getDebugger().getDT(tup).getAttribute("opEx_addedTup")

        if addedTup is not None:
            inputDt = retrieveStoredDTRef(self, tup, "opEx_addedTup")

            if inputDt is not None:
                self.buffer.append(inputDt.getTuple(True))

        else:  # Tuple to redo completed the buffer
            self.buffer.clear()
