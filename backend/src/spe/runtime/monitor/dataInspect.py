from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Callable, Any

from spe.common.dataType import DataType
from spe.common.timer import Timer
from spe.pipeline.operators.operatorDB import getDisplayDataType
from spe.runtime.monitor.dataDisplayType import DataDisplayType
from streamVizzard import StreamVizzard


class DataInspect(ABC):
    MAX_CHILD_ENTRIES = 10
    ROOT_ENTRY_NAME = "root"

    class Entry:
        def __init__(self, name: str, dataType: str, dataAccessor: Callable[[str, Any], Any]):
            self.dataType = dataType
            self.name = name
            self.dataAccessor = dataAccessor

            self.children: List[DataInspect.Entry] = []
            self.childLookup: Dict[str, DataInspect.Entry] = {}
            self.omitted = 0  # How many child entries where omitted for size reasons

        def addChild(self, child: DataInspect.Entry) -> bool:
            if len(self.children) < DataInspect.MAX_CHILD_ENTRIES:
                self.children.append(child)
                self.childLookup[child.name] = child

                return True
            else:
                self.omitted += 1

                return False

        def getChild(self, name: str):
            return self.childLookup.get(name, None)

        def getInspectedData(self, data):
            return self.dataAccessor(self.name, data)

        def toJSON(self) -> Dict:
            return {"name": self.name, "dataType": self.dataType, "omitted": self.omitted,
                    "children": [c.toJSON() for c in self.children]}

        @staticmethod
        def getRootEntry(dataType: str):
            return DataInspect.Entry(DataInspect.ROOT_ENTRY_NAME, dataType, lambda n, x: x)

    class InspectionRes:
        def __init__(self):
            self.resData: Optional[Any] = None
            self.resType: Optional[DataDisplayType] = None
            self.resStruct: Optional[Dict] = None  # Contains data,cmd if changed

    def __init__(self):
        self._inspectCmdRaw = None  # Inspect command
        self._inspectedEntryChain: List[DataInspect.Entry] = []

        self._structCache: Optional[DataInspect.Entry] = None

        self._inspectDataType: Optional[DataDisplayType] = None

        self._lastStructureUpdateTime = 0

    @abstractmethod
    def _getStructure(self, data) -> Entry:
        ...  # Returns root entry

    def getInspectedData(self, inspectCmd: Optional[str], data) -> InspectionRes:
        res = DataInspect.InspectionRes()

        res.resStruct = self.handleStructure(data, inspectCmd)

        if len(self._inspectedEntryChain) == 0:  # No inspection
            return res

        resData = data

        # Follow data downwards the entry chain

        try:
            for c in self._inspectedEntryChain:
                resData = c.getInspectedData(resData)
        except Exception:
            res.resStruct = self.handleStructure(data, inspectCmd, True)  # Refresh

            return res

        # Reached target entry -> retrieve data type for it

        dt = DataType.retrieve(resData, False)

        # Currently, we do not detect potentially other inspect types (since there only exists one which is recursive)
        # Future Work: Could implement it generalizable to recursively detect and append more inspect types
        if self._inspectDataType is None or not self._inspectDataType.supportsType(dt):  # Search for type again
            self._inspectDataType = getDisplayDataType(dt) if dt is not None else None

        res.resType = self._inspectDataType
        res.resData = resData

        return res

    def handleStructure(self, data, selectCmd: Optional[str], forceUpdate: bool = False) -> Optional[Dict]:
        # Regularly recalculate structure/cmd in case it changed, and we did not run into display errors so far
        if Timer.currentRealTime() - self._lastStructureUpdateTime > StreamVizzard.getConfig().MONITORING_INSPECT_UPDATE_INTERVAL:
            forceUpdate = True

        if self._structCache is None or forceUpdate:
            self._structCache = self._getStructure(data)
            self._lastStructureUpdateTime = Timer.currentRealTime()

            validCmd = self._setInspectionCmd(selectCmd, forceUpdate)  # Get valid part of current cmd that still applies

            return {"data": self._structCache.toJSON(), "cmd": validCmd}  # Updated
        else:
            self._setInspectionCmd(selectCmd)

        return {}  # Not changed

    def _setInspectionCmd(self, selectCmd: Optional[str], force: bool = False) -> Optional[str]:
        if self._structCache is None:  # No structure found
            return None

        if selectCmd == self._inspectCmdRaw and not force:  # No change
            return None

        self._inspectCmdRaw = selectCmd
        self._inspectedEntryChain = []  # Reset

        if selectCmd is None:  # No inspection
            return self.ROOT_ENTRY_NAME

        selectionChain = selectCmd.split(">")

        currentEntry = self._structCache

        for c in selectionChain:
            if len(self._inspectedEntryChain) == 0 and c == self.ROOT_ENTRY_NAME:  # First item is root element
                continue

            if currentEntry is None:
                break

            currentEntry = currentEntry.getChild(c)

            if currentEntry is not None:
                self._inspectedEntryChain.append(currentEntry)

        self._inspectDataType = None  # Indicate to search again for type since it may have changed

        validCmd = ">".join([v.name for v in self._inspectedEntryChain])  # The valid part of the chain

        return self.ROOT_ENTRY_NAME + (">" + validCmd if len(self._inspectedEntryChain) > 0 else "")
