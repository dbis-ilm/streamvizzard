from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional, Any

from spe.runtime.debugger.bufferManager.debugTupleStorageInfo import DebugTupleStorageInfo
from spe.common.tuple import Tuple

if TYPE_CHECKING:
    from spe.runtime.debugger.operatorDebugger import OperatorDebugger


class DebugTuple:
    def __init__(self, debugger: OperatorDebugger, t: Tuple):
        self.uuid = str(uuid.uuid4().hex)

        self.debugger = debugger  # The operator that created the DT

        self._tuple = t  # Points to original data, original data should not change anymore after this point
        self._data = {}  # Extra data that is not stored to disk and should be small

        self._tupleMemorySize = self._tuple.calcMemorySize()  # Will not change anymore

        # --- Buffer Information ---

        self.storageInfo: Optional[DebugTupleStorageInfo] = None
        self.refCount = 0  # How many DS reference this DT

    def registerAttribute(self, name: str, attr: Any, uniqueForBranch: bool = False) -> DebugTuple:
        if self._data is None:  # Data was deleted
            return self

        # DTs might hold same attributes for multiple different branches in case the DT was involved in a continuation.
        # If the value needs to be unique for the branch (for example when using timestamps) add the branch to the ID.

        regBranch = "#" + str(self.debugger.getDebugger().getHistory().getCurrentBranchID()) if uniqueForBranch else ""

        self._data[name + regBranch] = attr

        return self

    def pinDT(self):
        self.debugger.getDebugger().getBufferManager().pinDT(self)

    def unpinDT(self):
        self.debugger.getDebugger().getBufferManager().unpinDT(self)

    def _requestData(self):
        self.debugger.getDebugger().getBufferManager().requestDT(self)

    def setTupleData(self, data: tuple, recalcSize: bool = False):
        self._tuple.data = data

        if recalcSize:
            oldSize = self._tupleMemorySize

            self._tupleMemorySize = self._tuple.calcMemorySize()

            self.debugger.getDebugger().getBufferManager().updateDT(self, self._tupleMemorySize - oldSize)

    def clearData(self):
        self._tuple.data = None

    def delete(self):
        self.clearData()
        self.storageInfo = None
        self.refCount = 0

        self._tuple = None

    # ---------------------------- GETTER ----------------------------

    def getTuple(self, includeData: bool = True, pinned: bool = False) -> Tuple:
        if pinned:
            self.pinDT()

        if includeData and not self.isLoaded():
            self._requestData()

        return self._tuple

    def getAttribute(self, name: str, default: Any = None, uniqueForBranch: bool = False):
        regBranch = "#" + str(self.debugger.getDebugger().getHistory().getCurrentBranchID()) if uniqueForBranch else ""

        return self._data.get(name + regBranch, default)

    def getMemorySize(self) -> int:
        return self._tupleMemorySize  # Value in bytes

    def isLoaded(self) -> bool:
        return self.storageInfo is None or self.storageInfo.isLoaded()
