from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional, Awaitable, Any, List

from spe.common.tuple import Tuple

if TYPE_CHECKING:
    from spe.pipeline.pipelineUpdates import PipelineUpdate
    from spe.runtime.debugger.operatorDebugger import OperatorDebugger
    from spe.runtime.debugger.debugTuple import DebugTuple


class DebugStepType(Enum):
    ON_TUPLE_TRANSMITTED = "onTTrans"  # When the result tuple of an operator is distributed over a connection
    ON_TUPLE_PROCESSED = "onTP"  # After an operator has processed a new tuple
    PRE_TUPLE_PROCESSED = "ptP"  # Before an operator processes a tuple
    ON_OP_EXECUTED = "opEx"  # After an operator has been executed
    ON_STREAM_PROCESS_TUPLE = "spS"  # When a stream processes the next tuple
    ON_SOURCE_PRODUCED_TUPLE = "pcT"  # When a source operator has produced a new tuple

    def isInitial(self) -> bool:
        return (self == DebugStepType.ON_SOURCE_PRODUCED_TUPLE
                or self == DebugStepType.ON_STREAM_PROCESS_TUPLE)

    @staticmethod
    def parse(name: str):
        for d in DebugStepType:
            if d.name == name:
                return d

        return None


class StepContinuation:
    def __init__(self, target: DebugStepType, func: Callable[[Tuple], Awaitable[Any]],
                 canCont: Optional[Callable[[Tuple], bool]] = None):
        self.target = target
        self.func = func
        self.canCont = canCont


class DebugStep:
    def __init__(self, debugger: OperatorDebugger, sType: DebugStepType, time: float, debugTuple: DebugTuple,
                 undoFunc: Optional[Callable], redoFunc: Optional[Callable], cont: Optional[StepContinuation]):

        self.debugger = debugger

        self.debugTuple = debugTuple  # This is the DT that results after the step

        self._registerDT(True)

        self.time = time

        # Set after registering
        self.localID = -1  # The step ID relative to the respective branch
        self.branchID = -1

        self.type = sType

        self._redoFunc = redoFunc
        self._undoFunc = undoFunc

        self.cont = cont

        self.pipelineUpdates: Optional[List[PipelineUpdate]] = None

    def getUniqueID(self) -> str:
        return str(self.branchID) + "#" + str(self.localID)

    def onDeletion(self):
        self._registerDT(False)

        self.debugger.onStepDeletion(self)

    def _registerDT(self, register: bool):
        self.debugTuple.refCount += (1 if register else -1)

    def registerPipelineUpdate(self, pu: PipelineUpdate):
        if self.pipelineUpdates is None:
            self.pipelineUpdates = []

        self.pipelineUpdates.append(pu)

    def hasUpdates(self) -> bool:
        return self.pipelineUpdates is not None

    def executeUndo(self, tup: Tuple):
        self.debugger.getDebugger().preDebugStepExecution(self)

        if self._undoFunc is not None:
            self._undoFunc(tup)

            # Send after execution to make sure UI has correct state after data is sent
            self.debugger.getDebugger().onDebugStepExecuted(self, True)

        # Undo pipeline changes from last to first after the step is undone
        if self.pipelineUpdates is not None:
            for pu in reversed(self.pipelineUpdates):
                pu.undo()

    def executeRedo(self, tup: Tuple):
        self.debugger.getDebugger().preDebugStepExecution(self)

        # Redo pipeline changes before the step is redone
        if self.pipelineUpdates is not None:
            for pu in self.pipelineUpdates:
                pu.redo()

        if self._redoFunc is not None:
            # Send before execution to make sure UI has correct state before data is sent
            self.debugger.getDebugger().onDebugStepExecuted(self, False)

            self._redoFunc(tup)

    def canContinueStep(self) -> bool:
        return self.cont is not None and (self.cont.canCont is None or self.cont.canCont(self.debugTuple.getTuple()))
