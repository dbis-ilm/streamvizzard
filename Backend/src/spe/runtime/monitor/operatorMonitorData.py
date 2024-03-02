from __future__ import annotations

import json
import logging
import traceback
from typing import Optional, TYPE_CHECKING

from spe.runtime.monitor.dataInspect import DataInspect

if TYPE_CHECKING:
    from spe.pipeline.operators.module import MonitorDataType
    from spe.pipeline.operators.operator import Operator


class OperatorMonitorData:
    def __init__(self, operator: Operator):
        self._operator = operator

        self._data = None  # Current data to display
        self._displayDataType: Optional[MonitorDataType] = None
        self._displayMode = 0
        self._displaySocket = 0

        self._settings = None

        self._inspect: Optional[DataInspect] = None

    def setData(self, data: tuple):
        if data is None:
            # Empty data tuple
            data = tuple([None] * (self._displaySocket + 1))

        if len(data) <= self._displaySocket or self._displaySocket < 0:  # No data or sockets to display
            return

        # Only store the part of the data that should be sent
        # Data monitor transformations should be immutable and not change orig data!
        self._data = data[self._displaySocket]

    def setDisplayMode(self, newSocket, newMode, newInspect, newSettings):
        # Reset data if display mode has changed
        if newSocket != self._displaySocket or newMode != self._displayMode:
            self._data = None

        self._displaySocket = newSocket
        self._displayMode = newMode

        self._settings = newSettings

        if self._inspect is not None:
            self._inspect.select(newInspect)

    def getDisplaySocket(self):
        return self._displaySocket

    def getDisplayMode(self):
        return self._displayMode

    def getSettings(self):
        return self._settings

    def getInspectData(self):
        return self._inspect.inspectRawData if self._inspect is not None else None

    def getDisplayData(self):
        if self._data is None:
            return None

        res = {}

        dataToDisplay = self._data  # Initial

        # If the current data still belongs to the data type don't search for type again
        if self._displayDataType is not None and self._displayDataType.isDataType(dataToDisplay):
            dataToDisplay = self._displayDataType.transform(dataToDisplay)  # TODO: This should be recursive in case of many transform DT?
        else:
            newType, dataToDisplay = self._findDisplayMode(dataToDisplay)

            if dataToDisplay is None:  # Not even an inspecting type found
                return {"dType": None}

            # Reset display mode if data type changed and if this is not initial setup
            if newType != self._displayDataType and self._displayDataType is not None:
                self._displayMode = 0

            self._displayDataType = newType
            self._inspect = newType.getInspectInstance() if newType.isInspectType() else None

        dataType = self._displayDataType

        # Handle data inspect

        if self._displayDataType.isInspectType():
            # Only send structure if it has changed, otherwise None
            structure = self._inspect.getStructureIfChanged(dataToDisplay)
            res["struc"] = json.loads(structure) if structure is not None else {}

            # If no selection than just return structure info
            if self._inspect.hasSelection():
                if self._inspect.wasInspectChanged(True):
                    newDisplayMode, dataToDisplay = self._findDisplayMode(self._inspect.getData(dataToDisplay))

                    if dataToDisplay is None:
                        res["dType"] = None
                        return res

                    self._inspect.inspectDataType = newDisplayMode
                else:
                    dataToDisplay = self._inspect.getData(dataToDisplay)  # TODO: we might lose transformation DT here (same as above)
            else:
                res["dType"] = None
                return res

            # Do not override self displayType since we are just inspecting data, not changing it
            dataType = self._inspect.inspectDataType

            if dataType is None:
                return res

        dataToDisplay = dataType.prepareForDisplayMode(self._displayMode, dataToDisplay, self._settings)

        res["data"] = dataToDisplay
        res["dType"] = dataType.getName()
        res["dMode"] = self._displayMode
        res["dSocket"] = self._displaySocket

        return res

    def _findDisplayMode(self, dataToDisplay):
        from spe.pipeline.operators.operatorDB import getDisplayDataType

        # Transform data until we reach a non transformation type
        while True:
            # Infer data type for display
            try:
                newDataType = getDisplayDataType(dataToDisplay)
            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())
                newDataType = None

            if newDataType is None:
                return None, None
            elif newDataType.isTransformType():
                try:
                    dataToDisplay = newDataType.transform(dataToDisplay)
                except Exception:
                    logging.log(logging.ERROR, traceback.format_exc())

                continue

            break

        return newDataType, dataToDisplay
