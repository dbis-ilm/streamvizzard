from __future__ import annotations

import json
import logging
import traceback
from typing import Optional, TYPE_CHECKING, Callable, Dict, Any

from spe.common.udfCompiler import instantiateUserDefinedFunction
from spe.pipeline.operators.operatorDB import getDisplayDataType
from spe.runtime.monitor.dataInspect import DataInspect
from utils.utils import extractTracebackErrorMsg

if TYPE_CHECKING:
    from spe.pipeline.operators.module import MonitorDataType
    from spe.pipeline.operators.operator import Operator


class OperatorMonitorData:
    def __init__(self, operator: Operator):
        self._operator = operator

        self._data = None  # Current data to display

        self._displaySocket = 0
        self._displayDataType: Optional[MonitorDataType] = None
        self._displayMode = 0
        self._displayModeSettings = None

        self._lastDataType: Optional[MonitorDataType] = None

        self._transformerCode: Optional[str] = None
        self._transformer: Optional[Callable] = None

        self._inspect: Optional[DataInspect] = None
        self._inspectCmd: Optional[str] = None

        # If we should inform the receiver, that the display mode change request was acknowledged
        self._ackUpdate = False

        self._initialized = False

    def setData(self, data: tuple):
        if data is None:
            # Empty data tuple
            data = tuple([None] * (self._displaySocket + 1))

        if len(data) <= self._displaySocket or self._displaySocket < 0:  # No data or sockets to display
            return

        # Only store the part of the data that should be sent
        # Data monitor transformations should be immutable and not change orig data!
        self._data = data[self._displaySocket]

    def setConfig(self, data: Dict):
        newSocket = data.get("socket", self._displaySocket)
        newMode = data.get("mode", self._displayMode)
        newSettings = data.get("settings", self._displayModeSettings)
        newTransformer = data.get("transformer", self._transformerCode)
        newInspect = data.get("inspect", self._inspect)  # TODO: Check UI to mak this persistent when starting new pipeline

        # If socket changed, we need to await new data before we can display it

        if newSocket != self._displaySocket:
            self._data = None

        # Reset if we switched socket or transformer (which might affect data)

        if newSocket != self._displaySocket or newTransformer != self._transformerCode:
            self._transformer = None
            self._inspect = None
            self._displayDataType = None

        self._displaySocket = newSocket
        self._displayMode = newMode
        self._displayModeSettings = newSettings
        self._transformerCode = newTransformer
        self._inspectCmd = newInspect

        if self._transformerCode is not None and self._transformer is None:
            self._transformer = instantiateUserDefinedFunction(self._operator, self._transformerCode)
        elif self._transformerCode is None:
            self._transformer = None

        self._ackUpdate = True

    def getDisplayData(self):
        if self._data is None:
            return None

        res = {"dSocket": self._displaySocket, "dType": None}

        if self._ackUpdate:
            res["ackUpdate"] = True

            self._ackUpdate = False

        dataToDisplay = self._data  # Initial

        # Try to apply configured data transformation

        if self._transformer is not None:
            try:
                dataToDisplay = self._transformer(self._data)
            except Exception:
                res["error"] = extractTracebackErrorMsg(True, -2)

                return res

        # If the current data still belongs to the data type don't search for type again
        if self._displayDataType is not None and self._displayDataType.isDataType(dataToDisplay):
            dataToDisplay = self._displayDataType.transform(dataToDisplay)  # TODO: This should be recursive in case of many transform DT?
        else:
            newType, dataToDisplay = self._findDisplayMode(dataToDisplay)

            if dataToDisplay is None:  # Not even an inspecting type found
                return res

            self._displayDataType = newType
            self._inspect = newType.getInspectInstance() if newType.isInspectType() else None

        dataType = self._displayDataType

        # Handle data inspect TODO: REWORK INSPECT (0 length lists drop out of ARRAY:IMG, ARRAY:NUMBER and dont recover)
        # TODO: Limit amount of data send to client for inspection

        if self._displayDataType.isInspectType():
            # Only send structure if it has changed, otherwise None
            structure = self._inspect.getStructureIfChanged(dataToDisplay)
            res["struct"] = json.loads(structure) if structure is not None else {}

            if self._inspectCmd is not None:
                self._inspect.select(self._inspectCmd)  # TODO: Optimizable

            # If no selection then just return structure info
            if self._inspect.hasSelection():
                if self._inspect.wasInspectChanged(True):
                    newDisplayMode, dataToDisplay = self._findDisplayMode(self._inspect.getData(dataToDisplay))

                    if dataToDisplay is None:
                        return res

                    self._inspect.inspectDataType = newDisplayMode
                else:
                    dataToDisplay = self._inspect.getData(dataToDisplay)  # TODO: we might lose compiler DT here (same as above)
            else:
                return res

            # Do not override self displayType since we are just inspecting data, not changing it
            dataType = self._inspect.inspectDataType

            if dataType is None:
                return res

        # Reset display mode if data type changed and (if this is not initial run or mode is not present in type)

        # TODO: is this reliable?
        if dataType != self._lastDataType and (self._initialized or not dataType.hasDisplayMode(self._displayMode)):
            self._displayMode = dataType.getDefaultDisplayModeID()
            self._displayModeSettings = None  # Switching modes implies a reset of settings (for user)

        dataToDisplay = dataType.prepareForDisplayMode(self._displayMode, dataToDisplay, self._displayModeSettings)

        res["data"] = dataToDisplay
        res["dType"] = dataType.getName()
        res["dMode"] = self._displayMode

        self._lastDataType = dataType
        self._initialized = True

        return res

    def _findDisplayMode(self, dataToDisplay: Any) -> tuple[Optional[MonitorDataType], Optional[Any]]:
        # Transform data until we reach a non compiler type
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
