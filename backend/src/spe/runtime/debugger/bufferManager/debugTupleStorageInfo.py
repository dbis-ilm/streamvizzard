from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from spe.runtime.debugger.bufferManager.dataChunk import DataChunk


class DebugTupleStorageInfo:
    def __init__(self, storageChunk: DataChunk, storageID: int):
        self.storageChunk = storageChunk  # Identifier of the chunk where this DT is stored
        self.storageID = storageID  # ID inside the storageChunk

        self.valid = True
        self.pinned = False

    def isLoaded(self) -> bool:
        return self.storageChunk.loaded
