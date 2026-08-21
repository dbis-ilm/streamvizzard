from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, Dict

from spe.common.timer import Timer
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
        def __init__(self, timestamp: float, executionDuration: float, outputSize: int):
            self.timestamp = timestamp  # In s
            self.executionDuration = executionDuration  # In ms
            self.outputSize = outputSize  # In bytes

            self.prevTimestamp = 0  # Calculated
            self.prevAvgExecutionDuration = 0  # Calculated
            self.prevAvgDataSize = 0  # Calculated

    def __init__(self, operator: Operator):
        self.EMA_WINDOW = StreamVizzard.getConfig().MONITORING_EMA_WINDOW

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

        self._timestamp = 0

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

    def _onTupleProcessed(self, tupleIn: Tuple, executionDuration: float):
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

            self._registerTuple(OperatorMonitor.Entry(Timer.currentTime(), max(0.0, executionDuration * 1000), tupleIn.calcMemorySize()), dt)

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

            t.prevTimestamp = self._timestamp
            t.prevAvgExecutionDuration = self._avgExecutionTime  # Store prev value for undo
            t.prevAvgDataSize = self._avgDataSize

            if self._totalTuples > 1:  # Can only apply EMA if we already have a value
                dt = t.timestamp - self._timestamp
                alpha = 1 - math.exp(-dt / self.EMA_WINDOW)

                self._avgExecutionTime = alpha * t.executionDuration + (1 - alpha) * self._avgExecutionTime
                self._avgDataSize = alpha * t.outputSize + (1 - alpha) * self._avgDataSize
            else:
                self._avgExecutionTime = t.executionDuration
                self._avgDataSize = t.outputSize

            self._timestamp = t.timestamp

        else:  # Revert the addition of the recent element [since EMA can't be undone]
            self._totalTuples -= 1

            self._timestamp = t.prevTimestamp
            self._avgExecutionTime = t.prevAvgExecutionDuration
            self._avgDataSize = t.prevAvgDataSize

    def getDisplayData(self) -> Optional[Dict]:
        if not self._sendData:
            return None

        start = Timer.currentRealTime()

        dd = self.data.getDisplayData()

        end = Timer.currentRealTime()

        if dd is not None:  # This does not contain raw JSON serialization duration which is performed in a batch later
            dd["dFetch"] = (end - start) * 1000

        return dd

    def getAvgExecutionTime(self):
        return self._avgExecutionTime

    def getAvgDataSize(self):
        return self._avgDataSize

    def getTotalTuples(self):
        return self._totalTuples

    def getLastProcessTime(self):
        return self._timestamp

    def getMonitor(self) -> PipelineMonitor:
        return self._monitor

    def configureDataSend(self, send: bool):
        self._sendData = send

    def isSendingData(self):
        return self._sendData
