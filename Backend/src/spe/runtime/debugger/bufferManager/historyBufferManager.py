from __future__ import annotations

import tempfile
from collections import deque
from typing import TYPE_CHECKING, Optional, Deque, Dict

from spe.runtime.debugger.bufferManager.dataChunk import DataChunk
from spe.runtime.debugger.debugStep import DebugStep
from spe.runtime.debugger.debugTuple import DebugTuple

if TYPE_CHECKING:
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger


class HistoryBufferManager:
    def __init__(self, debugger: PipelineDebugger):

        self._pipelineDebugger = debugger

        # Memory limit of each type (None = Infinite)
        self._mainMemoryLimit: Optional[int] = None  # In MBytes
        self._storageMemoryLimit: Optional[int] = None  # In MBytes

        # Current memory values in bytes
        self._currentMainMemorySize = 0
        self._currentStorageMemorySize = 0

        # Lists Chunks that are currently resident in the main memory cache [LRU]
        self._chunkCache: Deque[DataChunk] = deque()
        # Pinned Chunk are ensured to be loaded and do not count to the memory size to prevent deadlocks
        self._pinnedChunkCache: Dict[int, DataChunk] = dict()

        self._currentDataChunk: Optional[DataChunk] = None

        self._storageDir: Optional[tempfile.TemporaryDirectory] = None

        self._initialized = False

    # ------------------------------ INTERFACE ------------------------------

    def initialize(self):
        self._storageDir = tempfile.TemporaryDirectory()
        self._initialized = True

    def reset(self):
        if not self._initialized:
            return

        self._initialized = False

        # Clear storage

        for ck in self._chunkCache:
            ck.removeFromCache()

        self._chunkCache.clear()
        self._pinnedChunkCache.clear()

        self._currentMainMemorySize = 0
        self._currentStorageMemorySize = 0

        self._currentDataChunk = None

        self._storageDir.cleanup()  # This will clear all temporary files

    def changeMemoryLimit(self, mainMemorySize: Optional[int], storageMemorySize: Optional[int]):
        self._mainMemoryLimit = mainMemorySize
        self._storageMemoryLimit = storageMemorySize

    def registerStep(self, step: DebugStep):
        if not self._initialized:
            return

        # Register both DebugTuples [DT] if not yet stored

        addedToBuffer = False

        if step.prevDebugTuple is not None and step.prevDebugTuple.refCount == 1:
            self._cacheDTChunked(step, step.prevDebugTuple)
            addedToBuffer = True

        if step.debugTuple.refCount == 1:
            self._cacheDTChunked(step, step.debugTuple)
            addedToBuffer = True

        if addedToBuffer:
            self._adjustBuffer()

    def updateDT(self, dt: DebugTuple, deltaSize: float):
        if not self._initialized:
            return

        # This happens for process stream and execute operator steps in which cases
        # the resulting tuple is not known on registering the debug step.
        # If the cache is very small and the chunk is already on disk,
        # this operation involves a high effort (load and store data chunk)!

        chunk = dt.storageInfo.storageChunk

        if chunk.updateDT(dt, deltaSize, self._storageDir.name):
            if chunk.loaded and not chunk.pinned:
                self._currentMainMemorySize += deltaSize
            elif chunk.onDisk:
                self._currentStorageMemorySize += deltaSize

    def requestDT(self, dt: DebugTuple):
        if not self._initialized or dt.storageInfo is None:
            return

        chunk = dt.storageInfo.storageChunk

        if not dt.isLoaded() and chunk.onDisk:
            if chunk.loadFromDisk(self._storageDir.name):
                self._currentMainMemorySize += chunk.memorySize

                self._chunkCache.append(chunk)

                self._adjustBuffer()

    def pinDT(self, dt: DebugTuple):
        if not self._initialized or dt.storageInfo is None:
            return

        dt.storageInfo.storageChunk.pinDT(dt)

    def unpinDT(self, dt: DebugTuple):
        if not self._initialized or dt.storageInfo is None or not dt.storageInfo.pinned:
            return

        chunk = dt.storageInfo.storageChunk

        chunk.unpinDT(dt)

        if chunk.pinned and not chunk.hasPinnedDTs():
            self._unpinChunk(chunk, True)

            self._adjustBuffer()  # In case addition to buffer overflows

    def flushCache(self):
        for chunk in self._chunkCache:
            if not chunk.hasPinnedDTs():
                self._handleStoreChunkToDisk(chunk)

        self._adjustBuffer()

    def onPauseExecution(self):
        # Execution is paused, move all chunks that are not persistent on disk to disk
        # This is only necessary, if we already have data on disk because on traversal
        # unsaved chunks might evict chunks on disk and interfere with traversed state

        if self._currentStorageMemorySize > 0:  # TODO: WE NEED TO WAIT FOR COMPLETION BEFORE USER IS ALLOWED TO TRAVERSE / CONTINUE! (MAYBE ADD A LOCK TO BUFFER ACCESS?)
            self.flushCache()

    # -------------------------------- BUFFER -------------------------------

    def _cacheDTChunked(self, ds: DebugStep, dt: DebugTuple):
        # It might be possible that the objects in the tuple of the DT are referenced by DT of other operators (distribute).
        # This problem only occurs on a non-distributed execution where operators are executed on the same machine
        # and share references for performance reasons (less clone operations).
        # For this reason the issue can be ignored since the currentMainMemory reflects the memory size
        # how it would be for distributed and non optimized use cases [Maximum/Worst Case].

        if self._currentDataChunk is None or self._currentDataChunk.branchID != ds.branchID:
            self._currentDataChunk = DataChunk(ds.branchID)
            self._chunkCache.append(self._currentDataChunk)

        if not self._currentDataChunk.tryAddDT(dt):
            self._currentDataChunk = DataChunk(ds.branchID)
            self._chunkCache.append(self._currentDataChunk)

            self._currentDataChunk.tryAddDT(dt)

        self._currentMainMemorySize += dt.getMemorySize()

    def _handleChunkCacheRemoval(self, removed: DataChunk, removeFromCacheQueue: bool):
        if removed == self._currentDataChunk:
            self._currentDataChunk = None

        if not removed.loaded:
            return

        if removeFromCacheQueue:
            self._chunkCache.remove(removed)

        # If this chunk has no pinned elements, we can safely remove it from cache

        if not removed.hasPinnedDTs():
            self._unpinChunk(removed, False)

            self._handleStoreChunkToDisk(removed)

            removed.removeFromCache()

            self._currentMainMemorySize -= removed.memorySize
        else:
            self._pinChunk(removed)

    def _handleStoreChunkToDisk(self, chunk: DataChunk):
        # Store to disk before removing data (if we have a disk storage)
        if not chunk.onDisk and self._storageMemoryLimit != 0:
            if chunk.storeToDisk(self._storageDir.name):
                self._currentStorageMemorySize += chunk.memorySize

    def _handleChunkDiskRemoval(self, removed: DataChunk):
        if not removed.onDisk:
            return

        if removed.removeFromDisk(self._storageDir.name):
            self._currentStorageMemorySize -= removed.memorySize

    def _handleDTRemoval(self, dt: DebugTuple):
        chunk = dt.storageInfo.storageChunk

        chunk.removeDT(dt)

        if not chunk.hasElements():
            self._handleChunkCacheRemoval(chunk, True)
            self._handleChunkDiskRemoval(chunk)

    def _removeOldestSteps(self) -> bool:
        removedSteps = self._pipelineDebugger.getHistory().removeOldestStep()

        if removedSteps is None:  # Not possible to remove anything (due to various reasons)
            return False

        for step in removedSteps:
            step.onDeletion()

            if step.debugTuple.refCount <= 0:
                self._handleDTRemoval(step.debugTuple)

            if step.prevDebugTuple is not None and step.prevDebugTuple.refCount <= 0:
                self._handleDTRemoval(step.prevDebugTuple)

        return True

    def _pinChunk(self, chunk: DataChunk):
        if chunk.pinned:
            return

        self._pinnedChunkCache[chunk.storageID] = chunk

        chunk.pinned = True

    def _unpinChunk(self, chunk: DataChunk, keepInCache: bool):
        if not chunk.pinned:
            return

        self._pinnedChunkCache.pop(chunk.storageID, None)

        chunk.pinned = False

        if keepInCache:
            self._chunkCache.append(chunk)

    def _adjustBuffer(self):
        # Check if cache needs adaptation
        if self._mainMemoryLimit is not None:
            cacheLimitBytes = self._mainMemoryLimit * 1000000

            while self._currentMainMemorySize > cacheLimitBytes:
                if len(self._chunkCache) == 0:  # Might happen if there are only pinned chunks left
                    break

                # If we can put chunks on disk we just remove first chunk from cache and offload it
                if self._storageMemoryLimit != 0:
                    removed = self._chunkCache.popleft()

                    self._handleChunkCacheRemoval(removed, False)
                else:  # If no disk storage is available we need to remove the oldest steps to free cache
                    if not self._removeOldestSteps():
                        return

        # Check if storage needs adaptation
        if self._storageMemoryLimit is not None:
            storageLimitBytes = self._storageMemoryLimit * 1000000

            while self._currentStorageMemorySize > storageLimitBytes:
                if not self._removeOldestSteps():
                    return

    # -------------------------------- GETTER --------------------------------

    def getMainMemorySize(self) -> int:
        # Returns value in MB
        return int(self._currentMainMemorySize / 1000000)

    def getStorageMemorySize(self) -> int:
        # Returns value in MB
        return int(self._currentStorageMemorySize / 1000000)

    def getPinnedMemorySize(self) -> int:
        total = 0

        for p in self._pinnedChunkCache.values():
            if not p.onDisk:
                total += p.memorySize

        return int(total / 1000000)

    def getTotalDataSize(self):
        totalCache = 0

        for c in self._chunkCache:
            if not c.onDisk:
                totalCache += c.memorySize

        return totalCache / 1000000 + self.getStorageMemorySize() + self.getPinnedMemorySize()
