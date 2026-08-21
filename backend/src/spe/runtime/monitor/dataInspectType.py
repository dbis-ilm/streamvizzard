from __future__ import annotations

from typing import Optional, Type, List

from spe.runtime.monitor.dataInspect import DataInspect
from spe.runtime.monitor.dataDisplayType import DataDisplayType


class DataInspectType(DataDisplayType):
    def __init__(self, name: str, dataTypes: List[DataDisplayType.TypeEntry], inspector: Type[DataInspect]):
        super().__init__(name, dataTypes)

        self._inspector: Optional[Type[DataInspect]] = inspector

    def getInspectInstance(self) -> DataInspect:
        return self._inspector()
