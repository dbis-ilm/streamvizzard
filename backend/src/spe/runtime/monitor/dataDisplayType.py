from __future__ import annotations

import logging
import traceback
from typing import Callable, Optional, Dict, List

from spe.common.dataType import DataType


class DataDisplayType:
    class TypeEntry:
        def __init__(self, dataType: DataType, shallow: bool = False):
            self.dataType = dataType
            self.shallow = shallow

    def __init__(self, name: str, dataTypes: List[TypeEntry]):
        self._name = name

        self._dataTypes = dataTypes

        self._displayModes: Dict[int, Callable] = dict()

    def supportsType(self, dt: DataType) -> bool:
        for st in self._dataTypes:
            if st.dataType.isEquals(dt, shallow=st.shallow):
                return True

        return False

    def registerDisplayMode(self, mode: int, func: Callable):
        # Make sure that the func does not modify the original input data! Create a copy if required
        self._displayModes[mode] = func

    def getName(self) -> str:
        return self._name

    def getDefaultDisplayModeID(self) -> int:
        if len(self._displayModes) == 0:
            return 0

        return list(self._displayModes.keys())[0]

    def hasDisplayMode(self, dMode: int) -> bool:
        prep = self._displayModes.get(dMode, None)

        return prep is not None

    def prepareForDisplayMode(self, dMode: int, data, settings: Optional[Dict]):
        prep = self._displayModes.get(dMode, None)

        if prep is None:
            return data

        try:
            if settings is None:
                settings = {}

            return prep(data, settings)
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return None
