import asyncio
import json
from typing import Callable, List, Dict, Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.debugger.debugBreakpoint import DebugBreakpoint
from spe.runtime.debugger.debugStep import DebugStep, DebugStepType, StepContinuation
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.debugger.pipelineDebugger import PipelineDebugger
from spe.runtime.runtimeGateway import getDebugger
from spe.common.timer import Timer
from spe.common.tuple import Tuple


class OperatorDebugger:
    def __init__(self, operator: Operator):
        self._debugger = getDebugger()

        self._operator = operator

        self._dtLookup: Dict[str, DebugTuple] = dict()  # Stores DT for each Tuple (uuid)
        self._lastSteps: Dict[DebugStepType, Optional[DebugStep]] = dict()  # Stores the last DS for each identifier

        self._lastRegisteredStep: Optional[DebugStep] = None  # The last step that was registered during execution
        self._currentStep: Optional[DebugStep] = None  # The current step this operator is in

        self._continuationEvent: Optional[asyncio.Event] = None
        self._continuationForceStep = False
        self._continuationFuture: Optional[asyncio.Future] = None

        self._breakPoints: Dict[DebugStepType, List[DebugBreakpoint]] = dict()
        self._stepCounter: Dict[DebugStepType, int] = dict()

    def reset(self, close: bool = False):
        self._dtLookup.clear()
        self._lastSteps.clear()
        self._lastRegisteredStep = None
        self._currentStep = None

        self._cancelContinuation()

        # Only reset breakpoints if pipeline is closed
        if close:
            self._breakPoints.clear()
            self._stepCounter.clear()

    async def registerStep(self, sType: DebugStepType, dt: DebugTuple, undo: Optional[Callable],
                           redo: Optional[Callable], cont: Optional[StepContinuation]) -> bool:

        currentTask = asyncio.current_task(loop=self.getOperator().getEventLoop())
        isContStep = getattr(currentTask, "contTask", False)

        forcedContStep = isContStep and self._continuationForceStep

        if not forcedContStep:  # ForceContStep is always allowed to pass
            if not isContStep:
                # Wait until current continuation(s) are completed before continuing to avoid original broker/source
                # execution chain executing parallel to the continuation chain (and missing event state).

                while self._continuationFuture is not None:
                    await asyncio.wait([self._continuationFuture])

                    # Future has been completed or was cancelled, otherwise loop with new future

                    if self._continuationFuture is not None and self._continuationFuture.done():
                        self._continuationFuture = None

                if not self._canRegister():
                    return True

            # Regular step registration, ensure pipeline is paused and only one task gets awakened & executed at once
            # when the pipeline is continued. Otherwise, starving tasks will interfere with the history after pausing.

            async with self._debugger.getHistoryEventLock():
                await self._debugger.getHistoryEvent().wait()

            if currentTask.cancelled():  # Ensure, that cancelled tasks never pass this
                return False

        # ---------------------------------- Register Step ---------------------------------

        if not self._canRegister():
            return True

        # Perform actual step registration

        step = DebugStep(self, sType, Timer.currentTime(), dt, undo, redo, cont)

        # Unpin last DT in case it's a different one than ours (also works for cont) which means, it's no longer used

        if self._lastRegisteredStep is not None and self._lastRegisteredStep.debugTuple != dt:
            self._lastRegisteredStep.debugTuple.unpinDT()

        self._lastRegisteredStep = step
        self._currentStep = step

        self._lastSteps[step.type] = step
        self._dtLookup[dt.getTuple(False).uuid] = dt

        self._debugger.registerGlobalStep(step)

        # Ensures, that this tuple is loaded and not evicted until its no longer used!
        dt.getTuple(True, True)

        # ------------------------------------------

        if forcedContStep:
            self._continuationForceStep = False
            self._continuationEvent.set()
        else:
            self._handleBreakpoint(sType, step)

        return True

    def _canRegister(self):
        # Ensure the debugger is not disabled or pipeline stopped
        return self._operator.isRunning() and self._operator.isDebuggingEnabled()

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

    def _handleBreakpoint(self, stepType: DebugStepType, ds: DebugStep):
        amount = self._stepCounter.get(stepType)

        amount = amount + 1 if amount is not None else 1

        self._stepCounter[stepType] = amount

        bp = self._breakPoints.get(stepType)

        if bp is not None:
            for i in range(0, len(bp)):
                p = bp[i]

                if p.isTriggered(stepType, amount):
                    getDebugger().triggerBreakpoint(ds, i)

                    break

    # ---------------------- HISTORY INTERFACES ----------------------

    def onTraversal(self, traversedStep: Optional[DebugStep], undo: bool, currentStep: Optional[DebugStep]):
        self._currentStep = currentStep  # Might be None if step does not belong to us

        # Adjust step counter for correct break point tracking

        if traversedStep is not None:
            prevStepCount = self._stepCounter.get(traversedStep.type, 0)

            self._stepCounter[traversedStep.type] = max(0, prevStepCount + (-1 if undo else 1))

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

    async def continueHistory(self):
        lastTypeSteps: Optional[Dict[DebugStepType, DebugStep]] = None

        # Find last steps from the current continuation position if not present

        if self._currentStep is None:
            lastTypeSteps, lastStep = self.getDebugger().getHistory().findLastStepOfTypes(self._operator.id, list(self._lastSteps.keys()))

            self._currentStep = lastStep

        # Update step lookups if we continue from different step

        if self._lastRegisteredStep is not self._currentStep:
            self._lastSteps.clear()

            if lastTypeSteps is None:
                lastTypeSteps, _ = self.getDebugger().getHistory().findLastStepOfTypes(self._operator.id, list(self._lastSteps.keys()))

            for stepType, step in lastTypeSteps.items():
                self._lastSteps[stepType] = step

        await self._performContinuation()

    async def _performContinuation(self):
        # Cancels existing process tasks and starts new to purge outdated operations.
        # New chain will await history event in its loop before starting.

        # TODO: Existing Race Condition: Operators might not yet have completed the step registration (reached barrier).
        #       However, for non-automated use this is almost impossible to happen.

        self._operator.continueExecution()

        # Executes continuation step and waits for completion.
        # This is important since operators without active waiting step will not be able to continue.
        # Also, we need to wait in order to not miss the continuation step on high frequency pipelines

        if self._currentStep is None or not self._currentStep.canContinueStep():
            # Might be None, if we traversed so far to the beginning that there is not prev step

            self._cancelContinuation()

            return

        # Blocks until the continuation step is executed (registered in the history)

        await self._continuationFunction(self._currentStep)

    async def _continuationFunction(self, contStep: DebugStep):
        self._continuationForceStep = True

        # Schedule continuation function to be executed on the loop.
        # The target step will be registered even if pipeline is paused to ensure that the continuation is finished.
        # Broker will wait until future is completed before processing a new tuple for the queue.

        self._continuationEvent = asyncio.Event()

        oldFuture = self._continuationFuture

        self._continuationFuture = asyncio.ensure_future(contStep.cont.func(contStep.debugTuple.getTuple()), loop=self.getOperator().getEventLoop())
        setattr(self._continuationFuture, "contTask", True)

        if oldFuture is not None:
            oldFuture.cancel()

        await self._continuationEvent.wait()

        self._continuationEvent = None

    def _cancelContinuation(self):
        if self._continuationFuture is not None:
            self._continuationFuture.cancel()
            self._continuationFuture = None

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
        return self._debugger
