from __future__ import annotations
from collections import deque
from typing import Optional, Deque, List

from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.debugger.history.historyState import HistoryState
from spe.runtime.runtimeGateway import getRuntimeManager
from spe.common.timer import Timer
from spe.common.tuple import Tuple
from streamVizzard import StreamVizzard


class ConnectionMonitor:
    class Entry:
        def __init__(self, timestamp: float):
            self.timestamp = timestamp

            self.removedEntries: Optional[List[ConnectionMonitor.Entry]] = None

            self.throughput = 0  # Calculated
            self.prevThroughput = 0  # Calculated

    def __init__(self, connection):
        self.SMOOTH = StreamVizzard.getConfig().MONITORING_OPERATOR_SMOOTH_FACTOR
        self.WINDOW = StreamVizzard.getConfig().MONITORING_CONNECTION_THROUGHPUT_WINDOW

        self._monitor = getRuntimeManager().gateway.getMonitor()
        self.connection = connection

        self._throughput = 0  # Calculated [tup/s]
        self._totalTuples = 0  # Counted

        self._tupleQueue: Deque[ConnectionMonitor.Entry] = deque()
        self._throughputTuples = 0

    def getTotalTuples(self):
        return self._totalTuples

    def getAvgThroughput(self):
        return self._throughput

    def registerTuple(self, t: Tuple):
        historyState = t.operator.getHistoryState()

        dt = t.operator.getDebugger().getDT(t) if t.operator.isDebuggingEnabled() else None

        if historyState == HistoryState.TRAVERSING_BACKWARD:
            self._undoRegister(dt)
        elif historyState == HistoryState.TRAVERSING_FORWARD:
            self._registerTuple(dt.getAttribute(f"cmData_{self.connection.id}", None, True), None)
        else:
            self._registerTuple(ConnectionMonitor.Entry(Timer.currentTime()), dt)

        self._monitor.onTupleTransmitted(self.connection)

    def _registerTuple(self, t: ConnectionMonitor.Entry, dt: Optional[DebugTuple]):
        self._throughputTuples += 1
        self._totalTuples += 1
        self._tupleQueue.append(t)

        # Remove entries outside the window range and register in monitor entry

        t.removedEntries = None

        while self._tupleQueue and self._tupleQueue[0].timestamp < t.timestamp - self.WINDOW:
            removed = self._tupleQueue.popleft()
            self._throughputTuples -= 1

            if t.removedEntries is None:
                t.removedEntries = [removed]
            else:
                t.removedEntries.append(removed)

        if dt is not None:
            dt.registerAttribute(f"cmData_{self.connection.id}", t, True)

        self._updateInternalStats(t, True)

    def _undoRegister(self, dt: DebugTuple):
        # Remove last element which was added by this step

        _ = self._tupleQueue.pop()
        self._totalTuples -= 1
        lastEntry: ConnectionMonitor.Entry = dt.getAttribute(f"cmData_{self.connection.id}", None, True)

        self._throughputTuples -= 1

        # Add entries again which where (potentially) removed by the undone step

        if lastEntry.removedEntries is not None:
            for removed in lastEntry.removedEntries:
                self._tupleQueue.appendleft(removed)
                self._throughputTuples += 1

        self._updateInternalStats(lastEntry, False)

    def _updateInternalStats(self, t: ConnectionMonitor.Entry, add: bool):
        # Calculate throughput of current sliding window

        t.throughput = 0

        if self._throughputTuples > 1:
            firstElement = self._tupleQueue[0]
            lastElement = self._tupleQueue[-1]

            duration = lastElement.timestamp - firstElement.timestamp

            t.throughput = (self._throughputTuples / duration) if duration > 0 else 0

        # Exponential Moving Average to smooth calculated throughput

        if add:
            t.prevThroughput = self._throughput  # Store prev value for undo

            if self._totalTuples > 1:  # Can only apply EMA if we already have a value
                self._throughput = self.SMOOTH * t.throughput + (1 - self.SMOOTH) * self._throughput
            else:
                self._throughput = t.throughput

        else:  # Revert the addition of the recent element [since EMA can't be undone]
            self._throughput = t.prevThroughput
