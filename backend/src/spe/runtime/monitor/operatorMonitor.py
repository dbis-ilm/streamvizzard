from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, Dict

from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.debugger.debuggingUtils import retrieveStoredDTRef
from spe.runtime.debugger.history.historyState import HistoryState
from spe.runtime.monitor.operatorMonitorData import OperatorMonitorData
from spe.runtime.runtimeGateway import getRuntimeManager
from spe.common.tuple import Tuple
from streamVizzard import StreamVizzard

if TYPE_CHECKING:
    from spe.runtime.monitor.pipelineMonitor import PipelineMonitor
    from spe.pipeline.operators.operator import Operator


class OperatorMonitor:
    class Entry:
        def __init__(self, executionDuration: float, outputSize: int):
            self.executionDuration = executionDuration  # In ms
            self.outputSize = outputSize  # In bytes

            self.prevAvgExecutionDuration = 0  # Calculated
            self.prevAvgDataSize = 0  # Calculated

        def __eq__(self, other):
            return (math.isclose(self.executionDuration, other.executionDuration)
                    and math.isclose(self.prevAvgExecutionDuration, other.prevAvgExecutionDuration)
                    and math.isclose(self.prevAvgDataSize, other.prevAvgDataSize)
                    and self.outputSize == other.outputSize)

        def __hash__(self):
            return id(self)

        def toJSON(self):
            return {"exDuration": self.executionDuration,
                    "outputSize": self.outputSize,
                    "prevAvgExecutionDuration": self.prevAvgExecutionDuration,
                    "prevAvgDataSize": self.prevAvgDataSize}

    def __init__(self, operator: Operator):
        self.SMOOTH = StreamVizzard.getConfig().MONITORING_OPERATOR_SMOOTH_FACTOR

        self._monitor = getRuntimeManager().gateway.getMonitor()

        self._operator = operator

        self._sendData = False

        self._currentTuple: Optional[Tuple] = None

        # Data
        self.data = OperatorMonitorData(self._operator)

        # Statistics

        self._totalTuples = 0
        self._avgExecutionTime = 0  # Calculated [ms]
        self._avgDataSize = 0  # Calculated [bytes]

        # Register listener
        self._operator.getEventListener().register(self._operator.EVENT_TUPLE_PROCESSED, self._onTupleProcessed)

    def setConfig(self, data: Dict):
        self.configureDataSend(data.get("enabled", self._sendData))

        displayCfg = data.get("displayConfig")

        if displayCfg is not None:
            self.data.setConfig(displayCfg)

    def notifyError(self, errorMsg: Optional[str]):
        # If error is None, the UI is informed to clear to error

        self._monitor.onOperatorError(self._operator, errorMsg)

    def _onTupleProcessed(self, tupleIn: Tuple, executionDuration):
        # tupleIn might be None if the very first process tuple DS is undone

        historyState = self._operator.getHistoryState()
        dt = self._operator.getDebugger().getDT(tupleIn) if tupleIn is not None and tupleIn.operator.isDebuggingEnabled() else None

        # ----- Display Data -----

        if self._sendData:
            displayTuple = tupleIn

            # Restore previous (if available), if we undo this tuple processing
            if historyState == HistoryState.TRAVERSING_BACKWARD and tupleIn is not None:
                prevDT = retrieveStoredDTRef(self._operator, tupleIn, "opMon_prevTup")

                displayTuple = prevDT.getTuple() if prevDT is not None else None

            self.data.setData(displayTuple.data if displayTuple is not None else None)

        # ----- Statistics -----

        if historyState == HistoryState.TRAVERSING_BACKWARD:
            self._undoRegister(dt)
        elif historyState == HistoryState.TRAVERSING_FORWARD:
            self._registerTuple(dt.getAttribute("omData", None, True), None)
        else:
            if dt is not None and self._currentTuple is not None:
                dt.registerAttribute("opMon_prevTup", self._currentTuple.uuid)

            self._registerTuple(OperatorMonitor.Entry(max(0, executionDuration * 1000), tupleIn.calcMemorySize()), dt)

        self._currentTuple = tupleIn

        self._monitor.onTupleProcess(self._operator)

    def _registerTuple(self, t: OperatorMonitor.Entry, dt: Optional[DebugTuple]):
        self._updateInternalStats(t, True)

        if dt is not None:
            dt.registerAttribute("omData", t, True)

    def _undoRegister(self, dt: DebugTuple):
        # Remove last element which was added by this step

        elmToRemove = dt.getAttribute("omData", None, True)

        self._updateInternalStats(elmToRemove, False)

    def _updateInternalStats(self, t: OperatorMonitor.Entry, add: bool):
        # Exponential Moving Average, no need to remove the oldest values since their influence diminishes over time

        if add:
            self._totalTuples += 1

            t.prevAvgExecutionDuration = self._avgExecutionTime  # Store prev value for undo
            t.prevAvgDataSize = self._avgDataSize

            if self._totalTuples > 1:  # Can only apply EMA if we already have a value
                self._avgExecutionTime = self.SMOOTH * t.executionDuration + (1 - self.SMOOTH) * self._avgExecutionTime
                self._avgDataSize = self.SMOOTH * t.outputSize + (1 - self.SMOOTH) * self._avgDataSize
            else:
                self._avgExecutionTime = t.executionDuration
                self._avgDataSize = t.outputSize

        else:  # Revert the addition of the recent element [since EMA can't be undone]
            self._totalTuples -= 1

            self._avgExecutionTime = t.prevAvgExecutionDuration
            self._avgDataSize = t.prevAvgDataSize

    def getDisplayData(self):
        if not self._sendData:
            return None

        return self.data.getDisplayData()

    def getAvgExecutionTime(self):
        return self._avgExecutionTime

    def getAvgDataSize(self):
        return self._avgDataSize

    def getTotalTuples(self):
        return self._totalTuples

    def getMonitor(self) -> PipelineMonitor:
        return self._monitor

    def configureDataSend(self, send: bool):
        self._sendData = send

    def isSendingData(self):
        return self._sendData
