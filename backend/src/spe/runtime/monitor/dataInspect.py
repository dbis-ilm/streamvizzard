import json
from abc import ABC, abstractmethod
from typing import Optional


class DataInspect(ABC):
    def __init__(self):
        self.inspectRawData = None
        self.inspectData = None

        self._inspectChanged = True  # Initially nothing set so we need to recheck

        self._structCache = None

        from spe.pipeline.operators.module import MonitorDataType
        self.inspectDataType: Optional[MonitorDataType] = None

    @abstractmethod
    def _selectInternal(self, selected):
        ...

    @abstractmethod
    def _getStructureInternal(self, data) -> json:
        ...

    @abstractmethod
    def getData(self, data):
        ...

    def select(self, selected):
        self.inspectRawData = selected
        self._selectInternal(selected)

        self._inspectChanged = True

    def getStructureIfChanged(self, data) -> json:
        # TODO: WE SHOULD CHECK IF DATA STRUCTURE CHANGED (costly) AND REUSE CACHE!

        # Only return structure if it was changed
        if self._structCache is None:
            self._structCache = self._getStructureInternal(data)

            return self._structCache

        return None

    def hasSelection(self):
        return self.inspectData is not None

    def wasInspectChanged(self, reset: bool = False):
        chg = self._inspectChanged

        if reset:
            self._inspectChanged = False

        return chg
