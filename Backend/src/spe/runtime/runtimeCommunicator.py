from __future__ import annotations

import json
from typing import Optional
from typing import TYPE_CHECKING

from config import MONITORING_ENABLED, DEBUGGER_ENABLED

if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger, HistoryState
    from spe.runtime.monitor.pipelineMonitor import PipelineMonitor


class RuntimeCommunicator:
    def __init__(self, serverManager, runtimeManager):
        from network.server import ServerManager

        from spe.runtime.monitor.pipelineMonitor import PipelineMonitor
        from spe.runtime.debugger.pipelineDebugger import PipelineDebugger

        self._serverManager: Optional[ServerManager] = serverManager
        self._runtimeManager: Optional[RuntimeManager] = runtimeManager

        self._monitor = PipelineMonitor(self._runtimeManager, self._serverManager) if MONITORING_ENABLED else None
        self._debugger = PipelineDebugger(self._runtimeManager, self._serverManager) if DEBUGGER_ENABLED else None

        global _instance
        _instance = self

    def onPipelineStarting(self):
        self._serverManager.sendSocketData(json.dumps({"cmd": "status", "status": "starting"}))

    def onPipelineStarted(self):
        self._serverManager.sendSocketData(json.dumps({"cmd": "status", "status": "started"}))

        if self._debugger is not None:
            self._debugger.startUp()

    def onPipelineStopping(self):
        if self._debugger is not None:
            self._debugger.shutdown()

        self._serverManager.clearSocketData()

        self._serverManager.sendSocketData(json.dumps({"cmd": "status", "status": "stopping"}))

    def onPipelineStopped(self):
        if self._monitor is not None:
            self._monitor.reset()

        if self._debugger is not None:
            self._debugger.close()

        from network.socketTuple import GenericSocketTuple
        self._serverManager.sendSocketData(GenericSocketTuple(json.dumps({"cmd": "status", "status": "stopped"}), lambda t: self._serverManager.clearSocketData()))

    # ---------------- Event Listener ----------------

    def onTupleProcessed(self, operator):
        if self._monitor is not None and self._runtimeManager.isRunning():
            self._monitor.onTupleProcess(operator)

    def onOperatorError(self, operator, errorMsg: str):
        if self._monitor is not None:  # Errors can occur on startup before pipeline is running!
            self._monitor.onOperatorError(operator, errorMsg)

    def onTupleTransmitted(self, operator):
        if self._monitor is not None and self._runtimeManager.isRunning():
            self._monitor.onTupleTransmitted(operator)

    def onOpMessageQueueChanged(self, operator):
        if self._monitor is not None and self._runtimeManager.isRunning():
            self._monitor.onOpMessageQueueChanged(operator)

    def onAdvisorSuggestion(self, operator, advisorSuggestions):
        ...

    # ---------------- Controls by user ----------------

    def changeHeatmap(self, hmType):
        if self._monitor is not None:
            self._monitor.setHeatmapType(hmType)

    def changeDebuggerStep(self, targetStep: int, targetBranch: int):
        if self._debugger is not None:
            self._debugger.changeDebuggerStep(targetStep, targetBranch)

    def requestDebuggerStep(self, targetBranch: int, targetTime: float):
        if self._debugger is not None:
            self._debugger.requestDebuggerStep(targetBranch, targetTime)

    def changeDebuggerState(self, historyActive: bool, historyRewind: Optional[int]):
        if self._debugger is not None:
            self._debugger.changeDebuggerState(historyActive, historyRewind)

    def changeDebuggerConfig(self, enabled: bool, memoryLimit: Optional[int], storageLimit: Optional[int],
                             historyRewindSpeed: float, historyRewindUseStepTime: bool):
        if self._debugger is not None:
            self._debugger.changeDebuggerConfig(enabled, memoryLimit, storageLimit, historyRewindSpeed, historyRewindUseStepTime)

    def toggleAdvisor(self, enabled: bool):
        ...

    # ---------------- Getter ----------------

    def isAdvisorEnabled(self) -> bool:
        return False

    def isDebuggerEnabled(self) -> bool:
        if self._debugger is not None:
            return self._debugger.isEnabled()

        return False

    def getDebugger(self) -> PipelineDebugger:
        return self._debugger

    def getMonitor(self) -> PipelineMonitor:
        return self._monitor

    def getHistoryState(self) -> Optional[HistoryState]:
        if self._debugger is not None:
            return self._debugger.getHistoryState()

        return None

    def getRuntimeManager(self):
        return self._runtimeManager


_instance: RuntimeCommunicator


def onTupleProcessed(operator):
    if _instance is not None:
        _instance.onTupleProcessed(operator)


def onOperatorError(operator, errorMsg: str):
    if _instance is not None:
        _instance.onOperatorError(operator, errorMsg)


def onTupleTransmitted(connection):
    if _instance is not None:
        _instance.onTupleTransmitted(connection)


def onOpMessageQueueChanged(connection):
    if _instance is not None:
        _instance.onOpMessageQueueChanged(connection)


def onAdvisorSuggestion(operator, advisorSuggestions):
    if _instance is not None:
        _instance.onAdvisorSuggestion(operator, advisorSuggestions)


def isAdvisorEnabled() -> bool:
    if _instance is not None:
        return _instance.isAdvisorEnabled()

    return False


def isDebuggerEnabled() -> bool:
    if _instance is not None:
        return _instance.isDebuggerEnabled()

    return False


def getDebugger() -> PipelineDebugger:
    if _instance is not None:
        return _instance.getDebugger()


def getPipelineMonitor() -> PipelineMonitor:
    if _instance is not None:
        return _instance.getMonitor()


def getRuntimeManager() -> RuntimeManager:
    if _instance is not None:
        return _instance.getRuntimeManager()


def getHistoryState() -> Optional[HistoryState]:
    if _instance is not None:
        return _instance.getHistoryState()

    return None
