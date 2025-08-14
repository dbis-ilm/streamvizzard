from __future__ import annotations

import asyncio
import json
import threading
from asyncio import CancelledError
from typing import TYPE_CHECKING, Optional, Dict

from network.socketTuple import GenericGetterSocketTuple, DebugStepGetterSocketTuple, HistoryBranchUpdateSocketTuple
from spe.runtime.debugger.bufferManager.historyBufferManager import HistoryBufferManager
from spe.runtime.debugger.history.historyRewinder import HistoryRewinder
from spe.runtime.debugger.history.historyState import HistoryState
from spe.runtime.debugger.history.pipelineHistory import PipelineHistory
from spe.runtime.debugger.history.pipelineHistoryBranch import PipelineHistoryBranch
from spe.runtime.debugger.pipelineUpdateHandler import PipelineUpdateHandler
from spe.common.runtimeService import RuntimeService
from spe.common.timer import Timer
from streamVizzard import StreamVizzard

if TYPE_CHECKING:
    from network.server import ServerManager
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.debugger.debugStep import DebugStep


class PipelineDebugger(RuntimeService):
    # It is important to synchronize the registerStep and changeDebugger function to
    # assure that the different threads to not interfere with each other

    def __init__(self, runtimeManager: RuntimeManager, serverManager: ServerManager):
        super().__init__(runtimeManager, serverManager)

        self._enabled = False

        # Reentrant Lock may be acquired multiple times by same thread (nested functions)
        self._historyLock = threading.RLock()

        self._historyEvent: Optional[asyncio.Event] = None
        self._historyEventLock: Optional[asyncio.Lock] = None

        self._currentGSSocketTuple: Optional[GenericGetterSocketTuple] = None
        self._currentHESocketTuple: Optional[DebugStepGetterSocketTuple] = None
        self._currentHGUSocketTuple: Optional[HistoryBranchUpdateSocketTuple] = None

        self._pipelineHistory = PipelineHistory(self)

        self._historyBufferManager = HistoryBufferManager(self)

        self._historyRewinder = HistoryRewinder(self)

        self._pipelineUpdateHandler = PipelineUpdateHandler(self)

        self._provenanceInspector = None
        if StreamVizzard.getConfig().DEBUGGER_PROV_INSPECTOR_ENABLED:
            from spe.runtime.debugger.provenance.provenanceInspector import ProvenanceInspector

            self._provenanceInspector = ProvenanceInspector(self)

    # ----------------------------- INTERFACE -----------------------------

    def onPipelineStarting(self):
        # Return if debugger is not enabled or already initialized
        if not self._enabled or self._historyEvent is not None:
            return

        self._pipelineHistory.initialize()
        self._historyBufferManager.initialize()

        if self._provenanceInspector is not None:
            self._provenanceInspector.initialize()

        self._historyEvent = asyncio.Event()
        self._historyEventLock = asyncio.Lock()
        self.runtimeManager.getEventLoop().call_soon_threadsafe(self._historyEvent.set)

        self._pipelineUpdateHandler.start(self.runtimeManager.getPipeline())

    def onPipelineStopping(self):
        # When the pipeline is ordered to shut down

        if self._historyEvent is not None:
            # Stop pipeline execution immediately
            self.runtimeManager.getEventLoop().call_soon_threadsafe(self._historyEvent.clear)

        self._historyRewinder.reset()

        # When the pipeline is ordered to stop
        self._pipelineHistory.shutdown()

        if self._provenanceInspector is not None:
            self._provenanceInspector.shutdown()

    def onPipelineStopped(self):
        # When the pipeline has been stopped completely
        self._historyEvent = None

        self.reset(True)

    def reset(self, close: bool = False):
        # Reset operator data, mainly important if debugger is activated/deactivated during execution
        for op in self.runtimeManager.getPipeline().getAllOperators():
            op.getDebugger().reset(close)

        self._historyRewinder.reset()

        if self._provenanceInspector is not None:
            self._provenanceInspector.reset()

        self._pipelineHistory.reset()
        self._historyBufferManager.reset()

        self._pipelineUpdateHandler.reset()

        self._currentGSSocketTuple = None
        self._currentHESocketTuple = None
        self._currentHGUSocketTuple = None

        self._enabled = False

    def registerGlobalStep(self, step: DebugStep) -> int:
        with self._historyLock:
            stepID = self._pipelineHistory.registerStep(step)

            self._historyBufferManager.registerStep(step)

            self._pipelineUpdateHandler.onDebugStepRegistered(step)  # This enriches the steps with update information

            if self._provenanceInspector is not None:
                self._provenanceInspector.onDebugStepRegistered(step)

            self._sendStepData()

            return stepID

    def onDebugStepExecuted(self, step: DebugStep, undo: bool):
        if self._currentHESocketTuple is None:
            self._currentHESocketTuple = DebugStepGetterSocketTuple(self._getCurrentHESocketData, self._onHESocketDataSent, step, undo)
            self.serverManager.sendSocketData(self._currentHESocketTuple)
        else:
            self._currentHESocketTuple.step = step
            self._currentHESocketTuple.undo = undo

    def preDebugStepExecution(self, ds: DebugStep):
        self._pipelineUpdateHandler.onDebugStepExecuted()

        # Flushes pipeline monitor and step execution socket data to avoid
        # race conditions with previously registered data tuples

        if ds.hasUpdates():
            self._currentHESocketTuple = None

            monitor = self.runtimeManager.gateway.getMonitor()

            if monitor is not None:
                monitor.flushMonitorData()

    def changeDebuggerStep(self, targetStep: int, targetBranch: int):
        if not self.isPipelineRunning():
            return

        self._historyRewinder.reset()

        self.setHistoryStep(targetStep, targetBranch)

    def requestDebuggerStep(self, targetBranch: int, targetTime: Optional[float]) -> Optional[Dict]:
        if not self.isPipelineRunning() or not self._pipelineHistory.getHistoryState().isActive():
            return None

        stp = self._pipelineHistory.findClosestStepForTime(targetBranch, targetTime)

        return {"stepID": stp.localID if stp is not None else 0, "branchID": stp.branchID}

    def changeDebuggerState(self, historyActive: bool, historyRewind: Optional[int]):
        if not self.isPipelineRunning():
            return

        self._historyRewinder.reset()  # Cancel old rewind

        if historyActive:
            self._activateHistory(False)

            if historyRewind is not None:
                self._historyRewinder.start(historyRewind == 1)

        else:
            self._deactivateHistory()

    def changeDebuggerConfig(self, enabled: bool, memoryLimit: Optional[int], storageLimit: Optional[int],
                             historyRewindSpeed: float, historyRewindUseStepTime: bool, provenanceEnabled: bool,
                             provenanceAwaitUpdates: bool):
        self._historyBufferManager.changeMemoryLimit(memoryLimit, storageLimit)

        self._historyRewinder.setSpeed(historyRewindSpeed, historyRewindUseStepTime)

        if not enabled:
            self._historyRewinder.reset()

        if self._provenanceInspector is not None:
            self._provenanceInspector.changeConfig(provenanceAwaitUpdates)

            if not enabled:
                self._provenanceInspector.reset()
            else:
                if provenanceEnabled:
                    self._provenanceInspector.enable()
                else:
                    self._provenanceInspector.disable()

        prevEnabled = self._enabled
        self._enabled = enabled

        if prevEnabled and not enabled:
            with self._historyLock:
                self.onPipelineStopping()
                self.reset()

                # Continue regular pipeline execution
                self.runtimeManager.getEventLoop().call_soon_threadsafe(self._historyEvent.set)
        elif not prevEnabled and enabled:
            # Re-Initialize debugger
            self.onPipelineStarting()

    def executeProvenanceQuery(self, queryData: Dict):
        if self._provenanceInspector is not None and self._provenanceInspector:
            self._provenanceInspector.queryFromTemplate(queryData)

    # ---------------------------- GLOBAL STEP ----------------------------

    def _sendStepData(self):
        if self._currentGSSocketTuple is None:
            self._currentGSSocketTuple = GenericGetterSocketTuple(self._getCurrentGSSocketData,
                                                                  self._onGSSocketDataSent)
            self.serverManager.sendSocketData(self._currentGSSocketTuple)

    def _getCurrentGSSocketData(self):
        ls = self._pipelineHistory.getLastStepForCurrentBranch()
        fs = self._pipelineHistory.getFirstStepForCurrentBranch()

        currentBranch = self._pipelineHistory.getBranch(self._pipelineHistory.getCurrentBranchID())

        cs = self._pipelineHistory.getCurrentStep()

        if currentBranch is None:  # Closed TODO: BETTER SOLUTION FOR DETECTING IF STATE SHOULD BE SENT!
            return None

        return json.dumps({"cmd": "debuggerData",
                           "active": self._pipelineHistory.getHistoryState().isActive(),
                           "maxSteps": self._pipelineHistory.getMaxStepsForCurrentBranch(),
                           "stepID": cs.localID,
                           "branchID": currentBranch.id,
                           "stepTime": cs.time,
                           "branchStepOffset": currentBranch.stepIDOffset,
                           "memSize": self._historyBufferManager.getMainMemorySize(),
                           "diskSize": self._historyBufferManager.getStorageMemorySize(),
                           "branchStartTime": fs.time if fs is not None else 0,
                           "branchEndTime": ls.time if ls is not None else 0
                           })

    def _onGSSocketDataSent(self, tup):
        self._currentGSSocketTuple = None

    # ------------------------ HISTORY EXECUTION -------------------------

    def _activateHistory(self, eventThread: bool = False):
        # eventThread if called from same thread as asyncio loop

        if self._pipelineHistory.getHistoryState().isActive():  # If pipeline is already paused return
            return

        loop = self.getRuntimeManager().getEventLoop()

        # Immediately pauses pipeline

        if eventThread:
            self._historyEvent.clear()
        else:
            loop.call_soon_threadsafe(self._historyEvent.clear)

        # Block until pipeline pausing is completed

        try:
            if eventThread:
                self._pauseExecution()  # No need to wait since we are on the event thread and can just call the func
            else:
                async def asyncPause():
                    self._pauseExecution()

                fut = asyncio.run_coroutine_threadsafe(asyncPause(), loop)
                fut.result()  # Required to extract fut
        except CancelledError:  # Pipeline stopped
            ...

    def _pauseExecution(self):
        # Runs on the event loop synchronously
        self._historyEvent.clear()

        with self._historyLock:
            self._pipelineHistory.onHistoryActivated()

        self._pipelineUpdateHandler.onPauseExecution()

        self._historyBufferManager.onPauseExecution()

        self._sendStepData()

    def setHistoryStep(self, stepID: int, branchID: int):
        if not self._pipelineHistory.getHistoryState().isActive():
            return

        with self._historyLock:
            self._pipelineHistory.traverseToStep(stepID, branchID)

    def _deactivateHistory(self):
        if not self._pipelineHistory.getHistoryState().isActive():  # If pipeline is still running
            return

        # Block until pipeline continuation is completed

        try:
            asyncio.run_coroutine_threadsafe(self._continueExecution(), self.getRuntimeManager().getEventLoop()).result()
        except CancelledError:  # Pipeline stopped
            ...

    async def _continueExecution(self):
        # Runs on the event loop synchronously

        with self._historyLock:
            # Reset timer to current step to have a consistent timing
            Timer.setTime(self._pipelineHistory.getCurrentStep().time)

            self._pipelineHistory.onHistoryDeactivated()

        # Notify operators

        for op in self.getRuntimeManager().getPipeline().getAllOperators():
            await op.getDebugger().continueHistory()

        self._historyEvent.set()  # Allows operators to continue executing

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
            self.serverManager.sendSocketData(self._currentHGUSocketTuple)
        else:
            self._currentHGUSocketTuple.addBranch(branch)

    def _onHGUSocketDataSent(self, tup):
        self._currentHGUSocketTuple = None

    # ---------------------------- BREAKPOINTS ---------------------------

    def triggerBreakpoint(self, ds: DebugStep, index: int):
        if self.getHistoryState() is HistoryState.INACTIVE:
            self._activateHistory(True)

        self.serverManager.sendSocketData(json.dumps({"cmd": "triggerBP",
                                                       "stepID": ds.localID,
                                                       "branchID": ds.branchID,
                                                       "op": ds.debugTuple.debugger.getOperator().id,
                                                       "type": ds.type.name,
                                                       "stepTime": ds.time,
                                                       "bpIndex": index}))

    # ------------------------------ GETTER ------------------------------

    def isEnabled(self) -> bool:
        return self._enabled

    def getHistory(self) -> PipelineHistory:
        return self._pipelineHistory

    def getHistoryEvent(self) -> asyncio.Event:
        return self._historyEvent

    def getHistoryEventLock(self) -> asyncio.Lock:
        return self._historyEventLock

    def getHistoryState(self) -> HistoryState:
        return self._pipelineHistory.getHistoryState()

    def getHistoryLock(self) -> threading.RLock:
        return self._historyLock

    def getLastGlobalStep(self) -> Optional[DebugStep]:
        return self._pipelineHistory.getLastStepForCurrentBranch()

    def getRuntimeManager(self) -> RuntimeManager:
        return self.runtimeManager

    def getProvInspector(self):
        return self._provenanceInspector

    def getBufferManager(self) -> HistoryBufferManager:
        return self._historyBufferManager

    def getServerManager(self):
        return self.serverManager
