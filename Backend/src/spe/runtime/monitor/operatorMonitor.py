from __future__ import annotations

import json
from collections import deque
from typing import TYPE_CHECKING, Optional, Deque

from config import MONITORING_OPERATOR_MAX_TUPLES
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.debugger.history.historyState import HistoryState
from spe.runtime.monitor.operatorMonitorData import OperatorMonitorData
from spe.runtime.monitor.operatorMonitorTuple import OperatorMonitorTuple
from spe.runtime.runtimeCommunicator import onTupleProcessed, getHistoryState, onOperatorError
from spe.runtime.structures.tuple import Tuple

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator


class OperatorMonitor:
    def __init__(self, operator: Operator):
        self._operator = operator

        self._sendData = True
        self._sendStats = False

        # Data
        self.data = OperatorMonitorData(self._operator)

        # Error
        self.errorMsg: Optional[str] = None

        # Statistics
        self._monitorData: Deque[OperatorMonitorTuple] = deque()

        self._avgExecutionTime = 0  # Calculated
        self._avgDataSize = 0  # Calculated

        # Register listener
        self._operator.getEventListener().register(self._operator.EVENT_TUPLE_PROCESSED, self._onTupleProcessed)

    def setCtrlData(self, data: json):
        if data is not None:
            self._setMonitorState(data["state"])

            if data["dMode"] is not None:
                self._setDisplayMode(data["dMode"])

    def getCtrlData(self) -> dict:
        return {"state": {"sendData": self._sendData,
                          "sendStats": self._sendStats},
                "dMode": {"socket": self.data.getDisplaySocket(),
                          "mode": self.data.getDisplayMode(),
                          "inspect": self.data.getInspectData(),
                          "settings": self.data.getSettings()}}

    def notifyError(self, errorMsg: str):
        # Error is also set here so the pipeline monitor can send the data when a tuple is produced
        # This allows the error to disappear when no new error is produced

        self.errorMsg = errorMsg

        onOperatorError(self._operator, errorMsg)

    def _onTupleProcessed(self, tupleIn: Tuple, executionDuration):
        # tupleIn might be None if the very first process tuple DS is undone

        if self._sendData:
            self.data.setData(tupleIn.data if tupleIn is not None else None)

        dt = tupleIn.operator.getDebugger().getDT(tupleIn) if tupleIn is not None and tupleIn.operator.isDebuggingEnabled() else None

        historyState = getHistoryState()

        if historyState == HistoryState.TRAVERSING_BACKWARD:
            self._undoRegister(dt)
        elif tupleIn is None:
            return
        elif historyState == HistoryState.TRAVERSING_FORWARD:
            self._registerTuple(dt.getAttribute("omData"), None)
        else:
            self._registerTuple(OperatorMonitorTuple(max(0, executionDuration * 1000), tupleIn.calcMemorySize()), dt)

        onTupleProcessed(self._operator)

    def _registerTuple(self, t: OperatorMonitorTuple, dt: Optional[DebugTuple]):
        self._monitorData.append(t)

        self._updateInternalStats(t, True)

        if len(self._monitorData) > MONITORING_OPERATOR_MAX_TUPLES:
            removed = self._monitorData.popleft()

            self._updateInternalStats(removed, False)

        if dt is not None:
            dt.registerAttribute("omData", t)

            # Register the now first element of the queue since this will be removed in next addition
            if len(self._monitorData) == MONITORING_OPERATOR_MAX_TUPLES:
                dt.registerAttribute("omLastE", self._monitorData[0])

    def _undoRegister(self, dt):
        # This element will be removed since it was added in the last step
        lastElm = self._monitorData.pop()
        self._updateInternalStats(lastElm, False)

        if dt is None:
            return

        # Check if we need to add the element that was removed during the undone register
        removed = dt.getAttribute("omLastE")
        if removed is not None:
            self._monitorData.appendleft(removed)
            self._updateInternalStats(removed, True)

    def _updateInternalStats(self, t: OperatorMonitorTuple, add: bool):
        qSize = len(self._monitorData)

        if qSize == 0:
            self._avgExecutionTime = 0
            self._avgDataSize = 0

            return

        self._avgExecutionTime = (self._avgExecutionTime * (qSize + (-1 if add else 1))
                                  + (t.executionDuration if add else -t.executionDuration)) / qSize

        self._avgDataSize = (self._avgDataSize * (qSize + (-1 if add else 1))
                             + (t.outputSize if add else -t.outputSize)) / qSize

    def getDisplayData(self):
        if not self._sendData:
            return None

        return self.data.getDisplayData()

    def resetStatistics(self):
        self._monitorData.clear()
        self._avgExecutionTime = 0

    def getAvgExecutionTime(self):
        return self._avgExecutionTime

    def getAvgDataSize(self):
        return self._avgDataSize

    def retrieveError(self):
        err = self.errorMsg
        self.errorMsg = None
        return err

    def isDataEnabled(self) -> bool:
        return self._sendData

    def isStatsEnabled(self) -> bool:
        return self._sendStats

    def _setMonitorState(self, state: json):
        self._sendData = state["sendData"]
        self._sendStats = state["sendStats"]

    def _setDisplayMode(self, changeData):
        newSocket = changeData["socket"]
        newMode = changeData["mode"]
        newInspect = changeData["inspect"]
        newSettings = changeData["settings"]

        self.data.setDisplayMode(newSocket, newMode, newInspect, newSettings)
