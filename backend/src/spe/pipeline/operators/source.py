import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from asyncio import Future
from collections import deque
from concurrent.futures import CancelledError
from typing import Optional, Deque

from spe.pipeline.operators.operator import Operator
from spe.runtime.debugger.debugMethods import debugMethod
from spe.runtime.debugger.debugStep import DebugStepType, StepContinuation
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.common.timer import Timer
from spe.common.tuple import Tuple


class Source(Operator, ABC):
    """
    Inputs: Source do not have any inputs
    Outputs: Sources only have one output

    Source child operators do not need to support debugging methods (onUndoProduce, onRedoProduce) for their custom
    internal data, since they run in background, and we only care for produced tuples which are stored separately.
    Moving backing in the history does not revert their internal states but only the tuples they produced so far...
    """

    class SourceTup:
        def __init__(self, data: tuple, exTime: float):
            self.data = data
            self.exTime = exTime

    def __init__(self, opID: int, socketsIn: int, socketsOut: int):
        super(Source, self).__init__(opID, socketsIn, socketsOut)

        # TODO: SET THROUGH UI (MAYBE PER SOURCE SEPARATELY)
        # If true, the source will continue receiving data even if the pipeline is paused
        # Care: False might not be possible for some sources like socket without missing data
        self._realTimeDataSources = True

        self._produceTask: Optional[Future] = None
        self._processTask: Optional[Future] = None

        self._queueEvent: Optional[asyncio.Event] = None
        self._produceEvent: Optional[asyncio.Event] = None

        self._dataQueue: Deque[Source.SourceTup] = deque()

        self._lastProduceTime: Optional[int] = None  # The last time data was produced by the child function
        self._lastTupleProducedTime: Optional[int] = None  # The last time the result tuple was actually emitted

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        # Not used in sources
        ...

    @abstractmethod
    def _runSource(self) -> Optional[tuple]:
        ...

    def getWaitingTupleCount(self) -> int:
        return len(self._dataQueue)

    # -------------------------- PIPE DEBUGGER -------------------------

    def continueExecution(self):
        super(Source, self).continueExecution()

        # Cancels process task to purge outdated operations

        self._processTask.cancel()

        self._processTask = asyncio.ensure_future(self._processTupleQueue(), loop=self.getEventLoop())

    async def _debugProduceTuple(self, resTup: Tuple, exTime: float):
        dt = DebugTuple(self._debugger, resTup)
        dt.registerAttribute("exTime", exTime)

        return await self._debugger.registerStep(DebugStepType.ON_SOURCE_PRODUCED_TUPLE, dt,
                                                 undo=lambda tup: self._undoRedoProd(tup, True),
                                                 redo=lambda tup: self._undoRedoProd(tup, False),
                                                 cont=StepContinuation(DebugStepType.ON_TUPLE_TRANSMITTED, self._distributeTuple))

    def _undoRedoProd(self, tup: Tuple, undo: bool):
        self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [tup, 0])

        dt = self.getDebugger().getDT(tup)

        if undo:
            self._dataQueue.appendleft(Source.SourceTup(tup.data, dt.getAttribute("exTime")))

            self._queueEvent.set()
        else:
            self._dataQueue.popleft()

            if len(self._dataQueue) == 0:
                self._queueEvent.clear()

    # ------------------------------------------------------------------

    def _produce(self, data: tuple):
        if not self.isRunning() or data is None:
            return

        exTime = 0
        
        # Here we need to look at the real time without adaptations since this loop runs in parallel to debugging
        if self._lastProduceTime is not None:
            exTime = Timer.currentRealTime() - self._lastProduceTime

        tup = Source.SourceTup(data, exTime)

        self.getEventLoop().call_soon_threadsafe(self._enqueueDataTuple, tup)

        if not self._realTimeDataSources:  # Sync with asyncio state, so we wait when pipeline is paused
            try:
                fut = asyncio.run_coroutine_threadsafe(self._produceEvent.wait(), self._eventLoop)
                fut.result()  # Required to extract fut
            except CancelledError:  # Thrown when source is closed
                ...

        self._lastProduceTime = Timer.currentRealTime()

    def _enqueueDataTuple(self, tup: SourceTup):
        if not self.isRunning():
            return

        self._dataQueue.append(tup)

        self._queueEvent.set()

    async def _processTupleQueue(self):
        try:
            while self.isRunning():
                if self.isDebuggingEnabled():
                    # In case the history is paused, wait for continuation, since undo triggers queueEvent.
                    # If the loop is canceled during continuation wait before pipeline is resumed.

                    await self.getDebugger().getDebugger().getHistoryEvent().wait()

                self._queueEvent.clear()

                while self._dataQueue:
                    if not self.isRunning():
                        return

                    self._produceEvent.clear()

                    exTime = self._dataQueue[0].exTime

                    await self._performProduceWait(exTime)

                    if not self.isRunning():
                        return

                    await self._handleProducedTuple(self.createTuple(()), exTime)

                if not self.isRunning():
                    return

                await self._queueEvent.wait()

        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

    @debugMethod(_debugProduceTuple)
    async def _handleProducedTuple(self, resTup: Tuple, exTime: float):
        sourceTup = self._dataQueue.popleft()

        resTup.eventTime = Timer.currentTime()
        resTup.data = sourceTup.data

        if self.isDebuggingEnabled():
            self.getDebugger().getDT(resTup).setTupleData(resTup.data, True)

        self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [resTup, exTime])

        self._produceEvent.set()

        await self._distributeTuple(resTup)

    async def _performProduceWait(self, exTime: float):
        wt = exTime

        if self._lastTupleProducedTime is not None:
            wt -= max(0, Timer.currentTime() - self._lastTupleProducedTime)

        # Micro sleeps < 1ms will slow down execution, actual sleep time depends on timer resolution!
        # TODO: We could try to improve the actual sleep by considering dif to scheduled sleep
        #       Problem: Sleep resolution is not able to keep up with high frequency data
        if wt >= 0.001:
            await asyncio.sleep(wt)

        self._lastTupleProducedTime = Timer.currentTime()

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super(Source, self).onRuntimeCreate(eventLoop)

        self._queueEvent = asyncio.Event()
        self._produceEvent = asyncio.Event()

        # Could be an option to use ProcessPool instead of ThreadPool for better GLI isolation [requires data pickle]
        self._produceTask = asyncio.ensure_future(eventLoop.run_in_executor(None, self._runSource), loop=eventLoop)
        self._processTask = asyncio.ensure_future(self._processTupleQueue(), loop=eventLoop)

    def onRuntimeDestroy(self):
        loop = self.getEventLoop()

        super(Source, self).onRuntimeDestroy()

        if self._produceTask is not None:
            self._produceTask.cancel()
            self._produceTask = None

        if self._processTask is not None:
            self._processTask.cancel()
            self._processTask = None

        self._queueEvent = None

        if self._produceEvent is not None:
            # Resume stopped tasks so that they can shut down gracefully
            loop.call_soon_threadsafe(self._produceEvent.set)
            self._produceEvent = None

        self._dataQueue.clear()
