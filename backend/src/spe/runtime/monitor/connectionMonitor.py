from collections import deque
from typing import Optional, Deque

from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.debugger.history.historyState import HistoryState
from spe.runtime.runtimeGateway import getRuntimeManager
from spe.common.timer import Timer
from spe.common.tuple import Tuple
from streamVizzard import StreamVizzard


class ConnectionMonitor:
    def __init__(self, connection):
        self._monitor = getRuntimeManager().gateway.getMonitor()
        self.connection = connection

        self.throughput = 0  # Calculated [tup/s]

        self._tupleQueue: Deque[tuple[float, int]] = deque()

        self.totalTuples = 0
        self._throughputTuples = 0

    def registerTuple(self, t: Tuple):
        historyState = t.operator.getHistoryState()

        if historyState == HistoryState.TRAVERSING_BACKWARD:
            self._undoTuple(t)
        elif historyState == HistoryState.TRAVERSING_FORWARD:
            self._redoTuple(t)
        else:
            dt = t.operator.getDebugger().getDT(t) if t.operator.isDebuggingEnabled() else None
            self._addThroughputTuple(1, Timer.currentTime(), dt)

        self._calcThroughput()

        self._monitor.onTupleTransmitted(self.connection)

    def _addThroughputTuple(self, count: int, timestamp: float, dt: Optional[DebugTuple]):
        self.totalTuples += count

        self._throughputTuples += count
        self._tupleQueue.append((timestamp, count))

        removed = None
        if len(self._tupleQueue) > StreamVizzard.getConfig().MONITORING_CONNECTIONS_MAX_THROUGHPUT_ELEMENTS:
            removed = self._tupleQueue.popleft()

            self._throughputTuples -= removed[1]

        if dt is not None:
            dt.registerAttribute("cmData" + str(self.connection.id), (timestamp, count), True)

            # Register removed element to be restored if this action is undone
            if removed is not None:
                dt.registerAttribute("cmLastE" + str(self.connection.id), removed, True)

    def _redoTuple(self, nextT: Tuple):
        dt = nextT.operator.getDebugger().getDT(nextT)
        data = dt.getAttribute("cmData" + str(self.connection.id), None, True)

        self._addThroughputTuple(data[1], data[0], None)

    def _undoTuple(self, nextT: Tuple):
        dt = nextT.operator.getDebugger().getDT(nextT)

        lastElm = self._tupleQueue.pop()

        self.totalTuples -= lastElm[1]
        self._throughputTuples -= lastElm[1]

        # Check if we need to add element that was removed by the add operation we undo
        removed = dt.getAttribute("cmLastE" + str(self.connection.id), None, True)
        if removed is not None:
            self._tupleQueue.appendleft(removed)

            self._throughputTuples += removed[1]

    def _calcThroughput(self):
        queueSize = len(self._tupleQueue)

        # Might happen after undo
        if queueSize == 0:
            self.throughput = 0
            return

        firstElement = self._tupleQueue[0]
        lastElement = self._tupleQueue[queueSize - 1]

        deltaTime = lastElement[0] - firstElement[0]

        # TODO: Calc should be based on time (e.g. 1 sec windows) and not on #tuples
        # One less tp since the first entry can only count as a starting time, otherwise tp is too high
        self.throughput = (max(0, (self._throughputTuples - 1)) / deltaTime) if deltaTime > 0 else 0
