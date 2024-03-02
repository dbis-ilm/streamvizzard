from __future__ import annotations

import asyncio
from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional, Awaitable, Any, List

from spe.runtime.structures.tuple import Tuple

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

    @staticmethod
    def parse(name: str):
        for d in DebugStepType:
            if d.name == name:
                return d

        return None


class DebugStep:
    def __init__(self, debugger: OperatorDebugger, sType: DebugStepType, time: float, debugTuple: DebugTuple,
                 prevDT: DebugTuple, undoFunc: Optional[Callable], redoFunc: Optional[Callable],
                 contFunc: Optional[Callable[[Tuple], Awaitable[Any]]]):

        self.debugger = debugger

        # DT that where processed by this step or before this step
        self.debugTuple = debugTuple  # This is the DT that results after the step (REDO)
        self.prevDebugTuple = prevDT  # This is the DT before the step (UNDO)

        self._registerDT(True)

        self.time = time

        # Set after registering
        self.localID = -1  # The step ID relative to the respective branch
        self.branchID = -1

        self.type = sType

        self._redoFunc = redoFunc
        self._undoFunc = undoFunc

        self._contFunc = contFunc

        self.pipelineUpdates: Optional[List[PipelineUpdate]] = None

    def getUniqueID(self) -> str:
        return str(self.branchID) + "#" + str(self.localID)

    def onDeletion(self):
        self._registerDT(False)

        self.debugger.onStepDeletion(self)

    def _registerDT(self, register: bool):
        self.debugTuple.refCount += (1 if register else -1)

        if self.prevDebugTuple is not None:
            self.prevDebugTuple.refCount += (1 if register else -1)

    def registerPipelineUpdate(self, pu: PipelineUpdate):
        if self.pipelineUpdates is None:
            self.pipelineUpdates = []

        self.pipelineUpdates.append(pu)

    def hasUpdates(self) -> bool:
        return self.pipelineUpdates is not None

    def executeUndo(self, pT: Tuple, nT: Tuple):
        self.debugger.getDebugger().preDebugStepExecution(self)

        if self._undoFunc is not None:
            self._undoFunc(pT, nT)

            # Send after execution to make sure UI has correct state after data is sent
            self.debugger.getDebugger().onDebugStepExecuted(self, True)

        # Undo pipeline changes from last to first after the step is undone
        if self.pipelineUpdates is not None:
            for pu in reversed(self.pipelineUpdates):
                pu.undo()

    def executeRedo(self, pT: Tuple, nT: Tuple):
        self.debugger.getDebugger().preDebugStepExecution(self)

        # Redo pipeline changes before the step is redone
        if self.pipelineUpdates is not None:
            for pu in self.pipelineUpdates:
                pu.redo()

        if self._redoFunc is not None:
            # Send before execution to make sure UI has correct state before data is sent
            self.debugger.getDebugger().onDebugStepExecuted(self, False)

            self._redoFunc(pT, nT)

    def executeContinue(self):
        if self._contFunc is not None:
            asyncio.ensure_future(self._continuationFunction(), loop=self.debugger.getOperator().getEventLoop())

    async def _continuationFunction(self):
        # Wait until pipeline execution is really continued, this is crucial to not get rejected by regStep in opDebugger
        await self.debugger.getDebugger().getHistoryAsyncioEvent().wait()

        await self._contFunc(self.debugTuple.getTuple())
