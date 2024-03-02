import json
from typing import Callable, List, Dict, Optional, Awaitable, Any

from spe.pipeline.operators.operator import Operator
from spe.runtime.debugger.debugBreakpoint import DebugBreakpoint
from spe.runtime.debugger.debugStep import DebugStep, DebugStepType
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.debugger.pipelineDebugger import PipelineDebugger
from spe.runtime.runtimeCommunicator import getDebugger
from spe.runtime.structures.timer import Timer
from spe.runtime.structures.tuple import Tuple


class OperatorDebugger:
    def __init__(self, operator: Operator):
        self._pipelineDebugger = getDebugger()

        self._operator = operator

        self._dtLookup: Dict[str, DebugTuple] = dict()  # Stores DT for each Tuple (uuid)
        self._lastSteps: Dict[DebugStepType, Optional[DebugStep]] = dict()  # Stores the last DS for each identifier

        self._lastRegisteredStep: Optional[DebugStep] = None  # The last step that was registered during execution
        self._currentStep: Optional[DebugStep] = None  # The current step this operator is in

        self._breakPoints: Dict[DebugStepType, List[DebugBreakpoint]] = dict()
        self._stepCounter: Dict[DebugStepType, int] = dict()

    def reset(self, close: bool = False):
        self._dtLookup.clear()
        self._lastSteps.clear()
        self._lastRegisteredStep = None
        self._currentStep = None

        # Only reset breakpoints if pipeline is closed
        if close:
            self._breakPoints.clear()
            self._stepCounter.clear()

    async def registerStep(self, sType: DebugStepType, dt: DebugTuple, undo: Optional[Callable],
                           redo: Optional[Callable],
                           cont: Optional[Callable[[Tuple], Awaitable[Any]]]) -> Optional[DebugStep]:

        wasWaiting = False

        if self._pipelineDebugger.getHistoryAsyncioEvent() is not None:
            wasWaiting = not self._pipelineDebugger.getHistoryAsyncioEvent().is_set()
            await self._pipelineDebugger.getHistoryAsyncioEvent().wait()

        if not self._operator.isRunning() or not self._operator.isDebuggingEnabled():
            return None  # In case after pipeline pausing the debugger is disabled or pipeline stopped

        # Analyse continuation, during the wait, the pipeline state (and current step) might have been modified

        lastRegStep = self._lastRegisteredStep

        if self._lastRegisteredStep is not self._currentStep:
            self._lastRegisteredStep = self._currentStep

            # We were in a waiting state when the history was adapted, discard original step
            # since we continue with the continuation step stored in the DS.
            # Otherwise, we are now executing new steps after continuation and continue

            if wasWaiting:
                return self._currentStep  # Returns continuation step and cancels execution (debugMethod)

        # Register new step

        step = DebugStep(self, sType, Timer.currentTime(), dt,
                         self.getLastDTForStep(sType), undo, redo, cont)

        # -------------- Register Step -------------

        # Unpin last DT in case it's a different one than ours (also works for cont) which means, it's no longer used

        if lastRegStep is not None and lastRegStep.debugTuple != dt:
            lastRegStep.debugTuple.unpinDT()

        self._lastRegisteredStep = step
        self._currentStep = step

        self._lastSteps[step.type] = step
        self._dtLookup[dt.getTuple(False).uuid] = dt

        stepID = self._pipelineDebugger.registerGlobalStep(step)

        # Ensures, that this tuple is loaded and not evicted until its no longer used!

        dt.getTuple(True, True)

        # ------------------------------------------

        self._handleBreakpoint(sType, stepID)

        return None

    # -------------------------- BREAKPOINTS -------------------------

    def registerBreakpoints(self, bp: json):
        self._breakPoints.clear()

        for d in bp:
            p = DebugBreakpoint(d["enabled"], DebugStepType.parse(d["type"]), d["amount"])

            lis = self._breakPoints.get(p.stepType)

            if lis is None:
                lis = []

            lis.append(p)

            self._breakPoints[p.stepType] = lis

    def exportBreakpoints(self):
        bps = []

        for bpList in self._breakPoints.values():
            if bpList is None:
                continue

            for bp in bpList:
                bps.append({"enabled": bp.enabled,
                            "type": bp.stepType.name,
                            "amount": bp.amount})

        return bps

    def _handleBreakpoint(self, stepType: DebugStepType, stepID: int):
        amount = self._stepCounter.get(stepType)

        amount = amount + 1 if amount is not None else 1

        self._stepCounter[stepType] = amount

        bp = self._breakPoints.get(stepType)

        if bp is not None:
            for i in range(0, len(bp)):
                p = bp[i]

                if p.isTriggered(stepType, amount):
                    getDebugger().triggerBreakpoint(stepID, self._operator.id, p, i)

                    break

    # ---------------------- HISTORY INTERFACES ----------------------

    def onTraversal(self, currentActiveStep: DebugStep):
        self._currentStep = currentActiveStep

    def onStepDeletion(self, ds: DebugStep):
        if self._currentStep == ds:
            self._currentStep = None

        if self._lastRegisteredStep == ds:
            self._lastRegisteredStep = None

        lastDs = self._lastSteps.get(ds.type, None)

        if lastDs == ds:
            del self._lastSteps[ds.type]

        if ds.debugTuple.refCount == 0:
            del self._dtLookup[ds.debugTuple.getTuple(False).uuid]

        if ds.prevDebugTuple is not None and ds.prevDebugTuple.refCount == 0:
            del self._dtLookup[ds.prevDebugTuple.getTuple(False).uuid]

    def continueHistory(self):
        if self._lastRegisteredStep is not self._currentStep:
            # Update the last step lookup since we continue from a different point in history

            lastSteps = self.getDebugger().getHistory().findLastStepOfTypes(self._operator.id,
                                                                            list(self._lastSteps.keys()))
            self._lastSteps.clear()

            for stepType, step in lastSteps.items():
                self._lastSteps[stepType] = step

            # Appends continuation to event loop, this is important since operators without active waiting step
            # registration will not be able to continue their current step

            self._currentStep.executeContinue()

            # Notify operator that history is continued if we continue from a different position
            # The actual execution of the continuation step is performed in debugMethods

            self._operator.onHistoryContinuation(self._currentStep)

    def getDT(self, tupleIn: Tuple) -> DebugTuple:
        return self.getDTByTupleID(tupleIn.uuid)

    def getDTByTupleID(self, tupID: str) -> DebugTuple:
        return self._dtLookup.get(tupID)

    def getLastStep(self) -> Optional[DebugStep]:
        return self._lastRegisteredStep

    def getLastStepForIdentifier(self, t: DebugStepType) -> Optional[DebugStep]:
        return self._lastSteps.get(t, None)

    def getLastDTForStep(self, stepType: DebugStepType) -> Optional[DebugTuple]:
        res = self._lastSteps.get(stepType, None)

        if res is not None:
            return res.debugTuple

        return None

    # ---------------------------- GETTER ----------------------------

    def getOperator(self):
        return self._operator

    def getDebugger(self) -> PipelineDebugger:
        return self._pipelineDebugger
