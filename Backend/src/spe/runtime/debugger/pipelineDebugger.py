from __future__ import annotations

import asyncio
import json
import threading
from typing import TYPE_CHECKING, Optional

import config
from network.socketTuple import GenericGetterSocketTuple, DebugStepGetterSocketTuple, HistoryBranchUpdateSocketTuple
from spe.runtime.debugger.bufferManager.historyBufferManager import HistoryBufferManager
from spe.runtime.debugger.debugBreakpoint import DebugBreakpoint
from spe.runtime.debugger.history.historyRewinder import HistoryRewinder
from spe.runtime.debugger.history.historyState import HistoryState
from spe.runtime.debugger.history.pipelineHistory import PipelineHistory
from spe.runtime.debugger.history.pipelineHistoryBranch import PipelineHistoryBranch
from spe.runtime.debugger.pipelineUpdateHandler import PipelineUpdateHandler
from spe.runtime.runtimeCommunicator import getPipelineMonitor
from spe.runtime.structures.timer import Timer

if TYPE_CHECKING:
    from network.server import ServerManager
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.debugger.debugStep import DebugStep


class PipelineDebugger:
    # It is important to synchronize the registerStep and changeDebugger function to
    # assure that the different threads to not interfere with each other

    def __init__(self, runtimeManager: RuntimeManager, serverManager: ServerManager):
        self._runtimeManager = runtimeManager
        self._serverManager = serverManager

        self._enabled = True

        # Reentrant Lock may be acquired multiple times by same thread (nested functions)
        self._historyLock = threading.RLock()

        self._historyAsyncioEvent: Optional[asyncio.Event] = None

        self._currentGSSocketTuple: Optional[GenericGetterSocketTuple] = None
        self._currentHESocketTuple: Optional[DebugStepGetterSocketTuple] = None
        self._currentHGUSocketTuple: Optional[HistoryBranchUpdateSocketTuple] = None

        self._pipelineHistory = PipelineHistory(self)

        self._historyBufferManager = HistoryBufferManager(self)

        self._historyRewinder = HistoryRewinder(self)

        self._pipelineUpdateHandler = PipelineUpdateHandler(self)

        self._provenanceInspector = None
        if config.DEBUGGER_PROV_INSPECTOR_ENABLED:
            from spe.runtime.debugger.provenance.provenanceInspector import ProvenanceInspector

            self._provenanceInspector = ProvenanceInspector(self)

    # ----------------------------- INTERFACE -----------------------------

    def startUp(self):
        self._pipelineHistory.initialize()
        self._historyBufferManager.initialize()

        if self._provenanceInspector is not None:
            self._provenanceInspector.initialize()

        self._historyAsyncioEvent = asyncio.Event()
        self._runtimeManager.getEventLoop().call_soon_threadsafe(self._historyAsyncioEvent.set)

        self._pipelineUpdateHandler.start(self._runtimeManager.getPipeline())

    def shutdown(self):
        if self._historyAsyncioEvent is not None:
            # Stop pipeline execution immediately
            self._runtimeManager.getEventLoop().call_soon_threadsafe(self._historyAsyncioEvent.clear)

        # When the pipeline is ordered to stop
        self._pipelineHistory.shutdown()

        self._historyRewinder.reset()  # First reset/stop rewinder in case it's still running!

        if self._provenanceInspector is not None:
            self._provenanceInspector.shutdown()

    def close(self):
        # When the pipeline has been stopped completely
        self._historyAsyncioEvent = None

        self.reset(True)

    def reset(self, close: bool = False):
        # Reset operator data, mainly important if debugger is activated/deactivated during execution
        for op in self._runtimeManager.getPipeline().getAllOperators():
            op.getDebugger().reset(close)

        self._pipelineHistory.reset()
        self._historyBufferManager.reset()

        self._pipelineUpdateHandler.reset()

        if self._provenanceInspector is not None:
            self._provenanceInspector.reset()

        self._currentGSSocketTuple = None
        self._currentHESocketTuple = None
        self._currentHGUSocketTuple = None

    def registerGlobalStep(self, step: DebugStep) -> int:
        with self._historyLock:
            stepID = self._pipelineHistory.registerStep(step)

            self._historyBufferManager.registerStep(step)

            self._pipelineUpdateHandler.onDebugStepRegistered(step)

            if self._provenanceInspector is not None:
                self._provenanceInspector.onDebugStepRegistered(step)

            self.sendStepData()

            return stepID

    def onDebugStepExecuted(self, step: DebugStep, undo: bool):
        if self._currentHESocketTuple is None:
            self._currentHESocketTuple = DebugStepGetterSocketTuple(self._getCurrentHESocketData, self._onHESocketDataSent, step, undo)
            self._serverManager.sendSocketData(self._currentHESocketTuple)
        else:
            self._currentHESocketTuple.step = step
            self._currentHESocketTuple.undo = undo

    def preDebugStepExecution(self, ds: DebugStep):
        self._pipelineUpdateHandler.onDebugStepExecuted()

        # Flushes pipeline monitor and step execution socket data to avoid
        # race conditions with previously registered data tuples

        if ds.hasUpdates():
            self._currentHESocketTuple = None
            getPipelineMonitor().flushMonitorData()

    def changeDebuggerStep(self, targetStep: int, targetBranch: int):
        if not self._pipelineHistory.getHistoryState().isActive():
            return

        self.setHistoryStep(targetStep, targetBranch)

    def requestDebuggerStep(self, targetBranch: int, targetTime: Optional[float]):
        if not self._pipelineHistory.getHistoryState().isActive():
            return

        stp = self._pipelineHistory.findClosestStepForTime(targetBranch, targetTime)

        self.getServerManager().sendSocketData(json.dumps({"cmd": "debReqStep",
                                                           "stepID": stp.localID if stp is not None else 0,
                                                           "branchID": stp.branchID}))

    def changeDebuggerState(self, historyActive: bool, historyRewind: Optional[int]):

        # If rewind is manually canceled or the history is resumed or the debugger is disabled we need to stop rewind
        rewindActive = (historyRewind is not None) and self._enabled and historyActive

        if self._historyRewinder.updateStatus(rewindActive, historyRewind == 1):
            return  # If rewinder already running we need to return since history is locked

        if historyActive:
            if self._historyAsyncioEvent.is_set():
                self._activateHistory()

            # Execute rewinder if enabled, this will lock history and prevent manual modifications
            # if self._historyRewinder.startMaybe():
            #     return

        elif self._historyAsyncioEvent is not None and not self._historyAsyncioEvent.is_set():
            self._deactivateHistory()

    def changeDebuggerConfig(self, enabled: bool, memoryLimit: Optional[int], storageLimit: Optional[int],
                             historyRewindSpeed: float, historyRewindUseStepTime: bool):
        self._historyBufferManager.changeMemoryLimit(memoryLimit, storageLimit)

        self._historyRewinder.setSpeed(historyRewindSpeed, historyRewindUseStepTime)

        if not enabled:
            self._historyRewinder.reset()

        with self._historyLock:
            self._enabled = enabled

            if not self.isEnabled():
                self.shutdown()
                self.reset()

                return

    # ---------------------------- GLOBAL STEP ----------------------------

    def sendStepData(self):
        if self._currentGSSocketTuple is None:
            self._currentGSSocketTuple = GenericGetterSocketTuple(self._getCurrentGSSocketData,
                                                                  self._onGSSocketDataSent)
            self._serverManager.sendSocketData(self._currentGSSocketTuple)

    def _getCurrentGSSocketData(self):
        ls = self._pipelineHistory.getLastStepForCurrentBranch()
        fs = self._pipelineHistory.getFirstStepForCurrentBranch()

        currentBranch = self._pipelineHistory.getBranch(self._pipelineHistory.getCurrentBranchID())

        if currentBranch is None:  # Closed
            return None

        return json.dumps({"cmd": "debuggerData",
                           "active": self._pipelineHistory.getHistoryState().isActive(),
                           "maxSteps": self._pipelineHistory.getMaxStepsForCurrentBranch(),
                           "stepID": self._pipelineHistory.getCurrentStepID(),
                           "branchID": currentBranch.id,
                           "branchStepOffset": currentBranch.stepIDOffset,
                           "memSize": self._historyBufferManager.getMainMemorySize(),
                           "diskSize": self._historyBufferManager.getStorageMemorySize(),
                           "rewindActive": self._historyRewinder.getStatus(),
                           "branchStartTime": fs.time if fs is not None else 0,
                           "branchEndTime": ls.time if ls is not None else 0
                           })

    def _onGSSocketDataSent(self, tup):
        self._currentGSSocketTuple = None

    # ------------------------ HISTORY EXECUTION -------------------------

    def _activateHistory(self):
        # Immediately pauses pipeline
        self._runtimeManager.getEventLoop().call_soon_threadsafe(self._historyAsyncioEvent.clear)

        with self._historyLock:
            self._pipelineHistory.onHistoryActivated()

        self._pipelineUpdateHandler.onPauseExecution()

        self._historyBufferManager.onPauseExecution()

        self.sendStepData()

    def setHistoryStep(self, stepID: int, branchID: int):
        with self._historyLock:
            self._pipelineHistory.traverseToStep(stepID, branchID)

    def _deactivateHistory(self):
        # Triggers continuation

        with self._historyLock:
            # Reset timer to current step to have a consistent timing
            Timer.setTime(self._pipelineHistory.getCurrentStep().time)

            self._pipelineHistory.onHistoryDeactivated()

        self._runtimeManager.getEventLoop().call_soon_threadsafe(self._historyAsyncioEvent.set)

    @staticmethod
    def _getCurrentHESocketData(step: DebugStep, undo: bool):
        # If step is and undo step the time will not reflect the time of the currently active step
        # If undo the active step at the time of the execution is the current step - 1

        return json.dumps({"cmd": "debuggerHistoryEx",
                           "stepID": step.localID - (1 if undo else 0),
                           "branchID": step.branchID,
                           "op": step.debugTuple.debugger.getOperator().id,
                           "undo": undo,
                           "type": step.type.name,
                           "stepTime": step.time})

    def _onHESocketDataSent(self, tup):
        self._currentHESocketTuple = None

    def onHistoryBranchUpdate(self, branch: PipelineHistoryBranch):
        if self._currentHGUSocketTuple is None:
            self._currentHGUSocketTuple = HistoryBranchUpdateSocketTuple(self._onHGUSocketDataSent, branch)
            self._serverManager.sendSocketData(self._currentHGUSocketTuple)
        else:
            self._currentHGUSocketTuple.addBranch(branch)

    def _onHGUSocketDataSent(self, tup):
        self._currentHGUSocketTuple = None

    # ---------------------------- BREAKPOINTS ---------------------------

    def triggerBreakpoint(self, stepID: int, opID: int, bp: DebugBreakpoint, index: int):
        if self.getHistoryState() is HistoryState.INACTIVE:
            self._activateHistory()

        self._serverManager.sendSocketData(json.dumps({"cmd": "triggerBP",
                                                       "stepID": stepID,
                                                       "op": opID,
                                                       "type": bp.stepType.name,
                                                       "bpIndex": index}))

    # ------------------------------ GETTER ------------------------------

    def isEnabled(self) -> bool:
        return self._enabled

    def getHistory(self) -> PipelineHistory:
        return self._pipelineHistory

    def getHistoryAsyncioEvent(self) -> asyncio.Event:
        return self._historyAsyncioEvent

    def getHistoryState(self) -> HistoryState:
        return self._pipelineHistory.getHistoryState()

    def getHistoryLock(self) -> threading.RLock:
        return self._historyLock

    def getLastGlobalStep(self) -> Optional[DebugStep]:
        return self._pipelineHistory.getLastStepForCurrentBranch()

    def getRuntimeManager(self) -> RuntimeManager:
        return self._runtimeManager

    def getProvInspector(self):
        return self._provenanceInspector

    def getBufferManager(self) -> HistoryBufferManager:
        return self._historyBufferManager

    def getServerManager(self):
        return self._serverManager
