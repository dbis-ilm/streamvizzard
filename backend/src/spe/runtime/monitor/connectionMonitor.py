from __future__ import annotations

import math
from collections import deque
from typing import Optional, Deque, List

from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.debugger.history.historyState import HistoryState
from spe.runtime.runtimeGateway import getRuntimeManager
from spe.common.timer import Timer
from spe.common.tuple import Tuple
from streamVizzard import StreamVizzard
from utils.utils import remap


class ConnectionMonitor:
    class Entry:
        def __init__(self, timestamp: float):
            self.timestamp = timestamp

            self.removedEntries: Optional[List[ConnectionMonitor.Entry]] = None

            self.prevThroughput = 0  # Calculated

    def __init__(self, connection):
        self.EMA_WINDOW = StreamVizzard.getConfig().MONITORING_EMA_WINDOW
        self.WINDOW_INTERVAL = StreamVizzard.getConfig().MONITORING_CONNECTION_WINDOW_INTERVAL
        self.WINDOW_COUNT = StreamVizzard.getConfig().MONITORING_CONNECTION_WINDOW_COUNT
        self.WINDOW_THRESHOLD = StreamVizzard.getConfig().MONITORING_CONNECTION_WINDOW_THRESHOLD

        self._monitor = getRuntimeManager().gateway.getMonitor()
        self.connection = connection

        self._throughput = 0  # Calculated [tup/s]
        self._totalTuples = 0  # Counted

        self._tupleQueue: Deque[ConnectionMonitor.Entry] = deque()

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
        self._totalTuples += 1
        self._tupleQueue.append(t)

        t.removedEntries = None

        # Dynamically determine the desired window size for calculating the tp. Big change since last time = small window
        # Tp dif is in percentage. Since its EMA, values are always smoothed out.

        lastTpDif = 0

        if len(self._tupleQueue) > 1:
            lastEntry = self._tupleQueue[-2]  # Prev active element
            lastTpDif = abs((self._throughput - lastEntry.prevThroughput) / lastEntry.prevThroughput * 100) if lastEntry.prevThroughput > 0 else 0

        maxQueueCount = int(remap(lastTpDif, 0.25, self.WINDOW_THRESHOLD, self.WINDOW_COUNT[1], self.WINDOW_COUNT[0], True))
        maxQueueInterval = remap(lastTpDif, 0.25, self.WINDOW_THRESHOLD, self.WINDOW_INTERVAL[1], self.WINDOW_INTERVAL[0], True)

        # Remove entries outside the window range and register in monitor entry
        # The window operates on a time- and count-based manner to also handle long delays between arrivals

        while (self._tupleQueue
               and len(self._tupleQueue) > maxQueueCount  # Count-based constraint
               and self._tupleQueue[0].timestamp < t.timestamp - maxQueueInterval):  # Time-based constraint
            removed = self._tupleQueue.popleft()

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

        # Add entries again which where (potentially) removed by the undone step

        if lastEntry.removedEntries is not None:
            for removed in reversed(lastEntry.removedEntries):
                self._tupleQueue.appendleft(removed)

        self._updateInternalStats(lastEntry, False)

    def _updateInternalStats(self, t: ConnectionMonitor.Entry, add: bool):
        # Calculate throughput of current sliding window

        if add:
            t.prevThroughput = self._throughput  # Store prev value for undo EMA

            queueTuples = len(self._tupleQueue)

            # Exponential Moving Average to smooth calculated throughput

            if queueTuples > 1:  # Can only apply EMA if we already have a valid entry calculated before
                # Total time captured within window (last - first)
                duration = max(self._tupleQueue[-1].timestamp - self._tupleQueue[0].timestamp, 1e-6)

                newTp = queueTuples / duration

                dt = t.timestamp - self._tupleQueue[-2].timestamp
                alpha = 1 - math.exp(-dt / self.EMA_WINDOW)

                self._throughput = alpha * newTp + (1 - alpha) * self._throughput

        else:  # Revert the addition of the recent element [since EMA can't be undone]
            self._throughput = t.prevThroughput
