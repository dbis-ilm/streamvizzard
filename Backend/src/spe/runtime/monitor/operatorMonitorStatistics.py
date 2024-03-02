from enum import Enum
from queue import Queue  # TODO: REMOVE QUEUE (DEQUE)
from typing import Optional, Dict

from config import MONITORING_OPERATOR_MAX_TUPLES
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.structures.timer import Timer


class OperatorStatisticType(Enum):
    EXECUTION_TIME = "ExTime"
    DATA_SIZE = "DataSize"
    CUSTOM = "Custom"


class OperatorStatisticEntry:
    def __init__(self):
        self.timestamp = 0

        self.values: Dict[str, float] = dict()

    def finalize(self):
        self.timestamp = Timer.currentTime()

    def addValue(self, key: str, value: float):
        self.values[key] = value


# TODO: WIP, Difficulties: Integration with Debugger
class OperatorMonitorStatistics:
    def __init__(self):
        self._entries: Queue[OperatorStatisticEntry] = Queue(0)

        self._averageValues: Dict[str, float] = dict()

        self._currentEntry = OperatorStatisticEntry()

    def registerEntry(self, dt: Optional[DebugTuple]):
        self._currentEntry.finalize()
        self._entries.put(self._currentEntry)

        self._updateInternalStats(self._currentEntry, True)

        if self._entries.qsize() > MONITORING_OPERATOR_MAX_TUPLES:
            removed = self._entries.get(False)  # Pop oldest

            self._updateInternalStats(removed, False)

        if dt is not None:
            dt.registerAttribute("omData", self._currentEntry)

            # Next register will drop last element, save it to restore
            if self._entries.qsize() == MONITORING_OPERATOR_MAX_TUPLES:
                dt.registerAttribute("omLastE", self._entries.queue[self._entries.qsize() - 1])

        self._currentEntry = OperatorStatisticEntry()

    def redoRegister(self, dt: Optional[DebugTuple]):
        self._currentEntry = dt.getAttribute("omData")
        self.registerEntry(None)

    def undoRegister(self, dt: Optional[DebugTuple]):
        # Construct new queue - omit last element, now our element should be last one
        # !! This presumes that we always the most recent point in history !!

        # This element will be removed since it was added in the last step
        lastElm = self._entries.queue[self._entries.qsize() - 1]

        newQ = Queue()

        # Check if we need to add element that was removed by next register
        removed = dt.getAttribute("omLastE")
        if removed is not None:
            newQ.put(removed)

        for i in range(0, self._entries.qsize() - 1):
            newQ.put(self._entries.queue[i])

        # Remove last element from stats
        if removed is not None:
            self._entries.put(removed)  # Dummy add value to match correct qSize for stat calc
            self._updateInternalStats(removed, True)

        self._entries = newQ

        self._updateInternalStats(lastElm, False)

    def reset(self):
        self._entries.queue.clear()
        self._averageValues.clear()

    def _updateInternalStats(self, e: OperatorStatisticEntry, add: bool):
        qSize = self._entries.qsize()

        # Update statistics

        for k, v in e.values:
            prevV = self._averageValues.get(k)

            if prevV is None:
                continue

            self._averageValues[k] = (prevV * (qSize + (-1 if add else 1)) + (v if add else -v)) / qSize

    def getAverage(self, key: str):
        return self._averageValues.get(key)
