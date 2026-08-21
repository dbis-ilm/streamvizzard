from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Callable, Dict

from spe.common.dataType import DataType, NoneType
from spe.common.udfCompiler import instantiateUserDefinedFunction
from spe.pipeline.operators.operatorDB import getDisplayDataType
from spe.runtime.monitor.dataInspect import DataInspect
from spe.runtime.monitor.dataInspectType import DataInspectType
from utils.utils import extractTracebackErrorMsg

if TYPE_CHECKING:
    from spe.runtime.monitor.dataDisplayType import DataDisplayType
    from spe.pipeline.operators.operator import Operator


class OperatorMonitorData:
    EMPTY_DATA = {}

    def __init__(self, operator: Operator):
        self._operator = operator

        self._data = None  # Current data to display

        self._displaySocket = 0
        self._displayDataType: Optional[DataDisplayType] = None
        self._displayMode = 0
        self._displayModeSettings = None

        self._lastDataType: Optional[DataDisplayType] = None

        self._transformerCode: Optional[str] = None
        self._transformer: Optional[Callable] = None

        self._inspector: Optional[DataInspect] = None
        self._inspectCmd: Optional[str] = None

        # If we should inform the receiver, that the display mode change request was acknowledged
        self._ackUpdate = False

        self._initialized = False

    def setData(self, data: tuple):
        self._data = None

        if data is None or len(data) <= self._displaySocket or self._displaySocket < 0:  # No data or sockets to display
            return

        # Only store the part of the data that should be sent
        # Data monitor transformations should be immutable and not change orig data!
        self._data = data[self._displaySocket]

        if self._data is None:  # Explicitly indicate empty data
            self._data = self.EMPTY_DATA

    def setConfig(self, data: Dict):
        newSocket = data.get("socket", self._displaySocket)
        newMode = data.get("mode", self._displayMode)
        newSettings = data.get("settings", self._displayModeSettings)
        newTransformer = data.get("transformer", self._transformerCode)
        newInspect = data.get("inspect", self._inspectCmd)

        # If socket changed, we need to await new data before we can display it

        if newSocket != self._displaySocket:
            self._data = None

        # Reset if we switched socket or transformer (which might affect data)

        if newSocket != self._displaySocket or newTransformer != self._transformerCode:
            self._transformer = None
            self._inspector = None
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

    def getDisplayData(self) -> Optional[Dict]:
        if self._data is None:
            return None

        res = {"dSocket": self._displaySocket, "dType": None}

        if self._ackUpdate:
            res["ackUpdate"] = True

            self._ackUpdate = False

        dataToDisplay = self._data if self._data is not self.EMPTY_DATA else None  # Initial

        # Try to apply configured data transformation

        if self._transformer is not None:
            try:
                # For performance reasons we do not clone the data here.
                # The transformer function must ensure, that the original data object in memory is not modified!
                dataToDisplay = self._transformer(self._data)
            except Exception:
                res["error"] = extractTracebackErrorMsg(True, -2)

                return res

        res["rawType"] = type(dataToDisplay).__name__

        dt = DataType.retrieve(dataToDisplay, False)

        if dt is None:  # Couldn't detect any data type
            return res

        # Keep current display type if we encounter None data (templates should handle it)

        if isinstance(dt, NoneType) and self._displayDataType is not None:
            dataType = self._displayDataType

            if dataType is None:  # No previous type
                return res

        # Perform data handling for display

        else:
            # Only search for type again if data does no longer belong to prev type
            if self._displayDataType is None or not self._displayDataType.supportsType(dt):
                newType = getDisplayDataType(dt)

                if newType is None:  # No type to display found
                    return res

                self._displayDataType = newType
                self._inspector = None

            dataType = self._displayDataType

            # Handle data inspect

            if isinstance(dataType, DataInspectType):
                if self._inspector is None:  # Initially instantiate
                    self._inspector = dataType.getInspectInstance()

                res["dType"] = dataType.getName()  # Add preliminary type information of inspect type

                inspectionRes = self._inspector.getInspectedData(self._inspectCmd, dataToDisplay)
                res["struct"] = inspectionRes.resStruct  # Only send structure if it has changed

                if inspectionRes.resData is None:  # No inspection selected/found
                    return res
                elif inspectionRes.resType is None:  # Inspected selection has no available data type
                    res["dType"] = None

                    return res

                dataType = inspectionRes.resType
                dataToDisplay = inspectionRes.resData

            # Reset display mode if data type changed and (if this is not initial run or mode is not present in type)

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
