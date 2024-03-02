import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from asyncio import Future
from collections import deque
from concurrent.futures import CancelledError
from typing import Optional, List, Deque

from spe.pipeline.operators.operator import Operator
from spe.runtime.debugger.debugMethods import debugMethod
from spe.runtime.debugger.debugStep import DebugStepType, DebugStep
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.structures.timer import Timer
from spe.runtime.structures.tuple import Tuple


class SourceTup:
    def __init__(self, data: tuple, exTime: float, produceTime: float, uniqueID: int):
        self.data = data
        self.exTime = exTime
        self.uniqueID = uniqueID
        self.produceTime = produceTime


class Source(Operator, ABC):
    """
    Inputs: Source do not have any inputs
    Outputs: Sources only have one output
    """

    def __init__(self, opID: int, socketsIn: int, socketsOut: int):
        super(Source, self).__init__(opID, socketsIn, socketsOut)

        # TODO: SET THROUGH UI (MAYBE PER SOURCE SEPARATELY)
        # If true, the source will continue receiving data even if the pipeline is paused
        # Care: False might not be possible for some sources like socket without missing data
        self._realTimeDataSources = True

        self._produceTask: Optional[Future] = None
        self._processTask: Optional[Future] = None

        self._queueEvent: Optional[asyncio.Event] = None
        self._dataQueue: Deque[SourceTup] = deque()

        self._produceEvent: Optional[asyncio.Event] = None

        self._replayTask: Optional[Future] = None
        self._replayCompletionEvent: Optional[asyncio.Event] = None

        self._lastTuple: Optional[SourceTup] = None
        self._lastProduceTime = 0  # The last time data was produced by the child function
        self._lastTupleProducedTime: Optional[int] = None  # The last time the result tuple was actually emitted

        self._uniqueTupCounter = 0
        self._lastProdID = 0
        self._produceHistoryQueue: Deque[SourceTup] = deque()

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        # Not used in sources
        ...

    @abstractmethod
    def _runSource(self) -> Optional[tuple]:
        ...

    def getProducedCount(self) -> int:
        return self._lastProdID

    def getWaitingTupleCount(self) -> int:
        return len(self._dataQueue)

    # -------------------------- PIPE DEBUGGER -------------------------

    def onHistoryContinuation(self, contStep: DebugStep):
        if self._replayTask is not None:
            self._replayTask.cancel()

        # Remove source tuples from history buffer that are no longer represented in the history
        historyStartTime = self.getDebugger().getDebugger().getHistory().getHistoryStartTime()

        while self._produceHistoryQueue:
            firstElm = self._produceHistoryQueue[0]

            if firstElm.produceTime < historyStartTime:
                self._produceHistoryQueue.popleft()
            else:
                break

        # Collect tuples to produce by looking into the production history

        tupToProduce: List[SourceTup] = []

        for tup in self._produceHistoryQueue:
            if tup.uniqueID > self._lastProdID:
                tupToProduce.append(tup)

        # Start replay

        self.getEventLoop().call_soon_threadsafe(self._replayCompletionEvent.clear)
        self._replayTask = asyncio.ensure_future(self._replayHistory(tupToProduce), loop=self.getEventLoop())

    async def _replayHistory(self, tuplesToProduce: List[SourceTup]):
        # Wait until pipeline is really continued

        await self.getDebugger().getDebugger().getHistoryAsyncioEvent().wait()

        # Perform replay

        for sourceTup in tuplesToProduce:
            if not self.isRunning():
                break

            # New tuple to not interfere with prev data attributes in DT
            # This leads to higher data volume which needs to be stored in bufferManager

            await self._performProduceWait(sourceTup.exTime)

            if not self.isRunning():
                return

            await self._handleProducedTuple(sourceTup, self.createTuple(sourceTup.data))

        # Check if there is a waiting tuple that might get lost during continuation, produce it again
        # We still need to wait the execution time. Original produce call will be canceled during continuation

        if self._lastTuple is not None:
            await self._performProduceWait(self._lastTuple.exTime)

            if not self.isRunning():
                return

            await self._handleProducedTuple(self._lastTuple, self.createTuple(self._lastTuple.data))

            self._lastTuple = None

        if not self.isRunning():
            return

        self._replayTask = None
        self._replayCompletionEvent.set()

    async def _debugProduceTuple(self, sourceTup: SourceTup, tup: Tuple):
        dt = DebugTuple(self._debugger, tup)
        dt.registerAttribute("exTime", sourceTup.exTime)
        dt.registerAttribute("uniqueProdID", sourceTup.uniqueID)

        return await self._debugger.registerStep(DebugStepType.ON_SOURCE_PRODUCED_TUPLE, dt,
                                                 undo=lambda pT, nT: self._undoRedoProd(pT, True),
                                                 redo=lambda pT, nT: self._undoRedoProd(nT, False),
                                                 cont=self._distributeTuple)

    def _undoRedoProd(self, tup: Tuple, undo: bool):
        if undo:
            self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [tup, 0])
        else:
            self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [tup, 0])

        if undo and tup is None:  # Undo first produced tuple
            self._lastProdID = 0

            return

        dt = self.getDebugger().getDT(tup)

        self._lastProdID = dt.getAttribute("uniqueProdID")

    # ------------------------------------------------------------------

    def _produce(self, data: tuple):
        if not self.isRunning() or data is None:
            return

        # Here we need to look at the real time without adaptations since this loop runs in parallel to debugging
        exTime = Timer.currentRealTime() - self._lastProduceTime

        tup = SourceTup(data, exTime, Timer.currentTime(), self._stepUniqueCounter())

        self._dataQueue.append(tup)

        if self.isDebuggingEnabled():
            self._produceHistoryQueue.append(tup)

        self.getEventLoop().call_soon_threadsafe(self._queueEvent.set)

        if not self._realTimeDataSources:  # Sync with asyncio state, so we wait when pipeline is paused
            try:
                asyncio.run_coroutine_threadsafe(self._produceEvent.wait(), self._eventLoop).result()
            except CancelledError:  # Thrown when source is closed
                ...

        self._lastProduceTime = Timer.currentRealTime()

    async def _processTupleQueue(self):
        try:
            while self.isRunning():
                self._queueEvent.clear()

                while self._dataQueue:
                    if not self.isRunning():
                        return

                    tup = self._dataQueue.popleft()

                    try:
                        await self._produceTuple(tup)
                    except CancelledError:  # Thrown when source is closed
                        break

                if not self.isRunning():
                    return

                await self._queueEvent.wait()
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

    async def _produceTuple(self, tup: SourceTup):
        self._produceEvent.clear()

        await self._replayCompletionEvent.wait()

        await self._performProduceWait(tup.exTime)

        if not self.isRunning():
            return

        self._lastTuple = tup

        await self._handleProducedTuple(tup, self.createTuple(tup.data))

        self._lastTuple = None

        if self._produceEvent is not None:
            self._produceEvent.set()

    @debugMethod(_debugProduceTuple)
    async def _handleProducedTuple(self, sourceTup: SourceTup, tup: Tuple):
        if not self.isRunning():
            return

        tup.eventTime = Timer.currentTime()

        self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [tup, sourceTup.exTime])
        self._lastProdID = sourceTup.uniqueID

        await self._distributeTuple(tup)

    async def _performProduceWait(self, exTime: float):
        wt = exTime

        if self._lastTupleProducedTime is not None:
            wt -= max(0, Timer.currentTime() - self._lastTupleProducedTime)

        # Micro sleeps < 1ms will slow down execution, actual sleep time depends on timer resolution!
        if wt > 0.001:
            await asyncio.sleep(wt)

        self._lastTupleProducedTime = Timer.currentTime()

    def _stepUniqueCounter(self):
        v = self._uniqueTupCounter
        self._uniqueTupCounter += 1
        return v

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super(Source, self).onRuntimeCreate(eventLoop)

        self._queueEvent = asyncio.Event()
        self._produceEvent = asyncio.Event()

        self._lastProduceTime = Timer.currentRealTime()

        self._replayCompletionEvent = asyncio.Event()
        eventLoop.call_soon_threadsafe(self._replayCompletionEvent.set)

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

        if self._replayTask is not None:
            self._replayTask.cancel()
            self._replayTask = None

        self._queueEvent = None

        if self._replayCompletionEvent is not None:
            # Resume stopped tasks so that they can shut down gracefully
            loop.call_soon_threadsafe(self._replayCompletionEvent.set)
            self._replayCompletionEvent = None

        if self._produceEvent is not None:
            # Resume stopped tasks so that they can shut down gracefully
            loop.call_soon_threadsafe(self._produceEvent.set)
            self._produceEvent = None

        self._dataQueue.clear()
        self._produceHistoryQueue.clear()
