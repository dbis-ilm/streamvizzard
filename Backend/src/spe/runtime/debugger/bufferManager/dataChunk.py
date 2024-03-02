from __future__ import annotations

import logging
import os
import traceback
import uuid
from typing import TYPE_CHECKING, List

import dill

from config import DEBUGGER_BUFFER_MANAGER_CHUNK_MAX_MEM_SIZE, DEBUGGER_BUFFER_MANAGER_CHUNK_MAX_TUP_COUNT
from spe.runtime.debugger.bufferManager.debugTupleStorageInfo import DebugTupleStorageInfo

if TYPE_CHECKING:
    from spe.runtime.debugger.debugTuple import DebugTuple


MAX_MEM = DEBUGGER_BUFFER_MANAGER_CHUNK_MAX_MEM_SIZE
MAX_TUP = DEBUGGER_BUFFER_MANAGER_CHUNK_MAX_TUP_COUNT


class DataChunk:
    def __init__(self, branchID: int):
        self.branchID = branchID
        self.storageID = str(uuid.uuid4().hex)

        self.dts: List[DebugTuple] = []
        self.memorySize = 0  # In bytes

        self.onDisk = False
        self.loaded = True
        self.pinned = False

        self._validCount = 0
        self._pinnedCount = 0

    def tryAddDT(self, dt: DebugTuple) -> bool:
        memS = dt.getMemorySize()
        elms = len(self.dts)

        # If there are no elements yet, always add first DT
        if elms != 0 and (self.memorySize + memS > MAX_MEM or elms + 1 > MAX_TUP):
            return False

        self.dts.append(dt)

        dt.storageInfo = DebugTupleStorageInfo(self, len(self.dts) - 1)

        self._validCount += 1

        self.memorySize += memS

        return True

    def updateDT(self, dt: DebugTuple, deltaSize: float, storageDir: str) -> bool:
        self.memorySize += deltaSize

        if self.onDisk:  # High effort: load and store data again
            print("NEEDED TO UPDATE DISK ...")
            loaded = self.loaded
            newData = dt.getTuple(False).data  # Don't pull data from disk, or we override new data

            if not self.loadFromDisk(storageDir):
                return False

            # Update new data
            dt.getTuple().data = newData

            if not self.storeToDisk(storageDir):
                return False

            if not loaded:
                self.removeFromCache()

        return True

    def removeDT(self, dt: DebugTuple):
        if dt.storageInfo.valid:
            dt.storageInfo.valid = False
            self._validCount -= 1

        if dt.storageInfo.pinned:
            dt.storageInfo.pinned = False
            self._pinnedCount -= 1

    def pinDT(self, dt: DebugTuple):
        if not dt.storageInfo.pinned:
            dt.storageInfo.pinned = True
            self._pinnedCount += 1

    def unpinDT(self, dt: DebugTuple):
        if dt.storageInfo.pinned:
            dt.storageInfo.pinned = False
            self._pinnedCount -= 1

    def hasPinnedDTs(self) -> bool:
        return self._pinnedCount > 0

    def hasElements(self) -> bool:
        return self._validCount > 0

    def removeFromCache(self):
        if not self.loaded:
            return

        for dt in self.dts:
            dt.clearData()

        self.loaded = False

    def removeFromDisk(self, storageDir: str) -> bool:
        if not self.onDisk:
            return False

        try:
            os.remove(os.path.join(storageDir, self.storageID))

            self.onDisk = False

            return True

        except Exception:
            print("ERR: COULDN'T REMOVE Chunk " + str(self.storageID) + " FROM DISK")
            logging.log(logging.ERROR, traceback.format_exc())

            return False

    def storeToDisk(self, storageDir: str) -> bool:
        if self.onDisk:
            return False

        if self.pinned:
            raise Exception("A Data Chunk can not be stored on disk if it's pinned! [Chunk: " + str(self.storageID) + "]")

        filePath = os.path.join(storageDir, self.storageID)  # construct the storage path

        try:
            with open(filePath, "wb") as h:  # TODO: IMPROVE PERFORMANCE BY ASYNC WRITES (Controversy)?
                data = [dt.getTuple().data for dt in self.dts]

                dill.dump(data, h)  # TODO: MAYBE OFFER CUSTOM FUNCTIONS FOR SERIALIZATION THAT ARE MORE EFFICIENT?

                self.onDisk = True

            return True
        except Exception:
            print("ERR: COULDN'T STORE DTs TO DISK IN CHUNK " + str(self.storageID) + "!")
            logging.log(logging.ERROR, traceback.format_exc())

            return False

    def loadFromDisk(self, storageDir: str) -> bool:
        if not self.onDisk:
            return False

        try:
            with open(os.path.join(storageDir, self.storageID), "rb") as h:
                data = dill.load(h)

                for vID in range(len(data)):
                    dt = self.dts[vID]

                    dtData = data[vID]

                    dt.setTupleData(dtData, False)

                self.loaded = True

                return True
        except Exception:
            print("ERR: COULDN'T LOAD DTs FROM CHUNK " + str(self.storageID) + " FROM DISK")
            logging.log(logging.ERROR, traceback.format_exc())

            return False
