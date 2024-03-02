import json
import numbers

from spe.pipeline.operators.base.dataTypes.figureD import FigureD
from spe.pipeline.operators.base.dataTypes.scatterplotD import ScatterplotD
from spe.pipeline.operators.base.operators.filter import Filter
from spe.pipeline.operators.base.operators.transform.combine import Combine
from spe.pipeline.operators.base.operators.transform.flattenList import FlattenList
from spe.pipeline.operators.base.operators.transform.parseJSON import ParseJSON
from spe.pipeline.operators.base.operators.transform.stringSplit import StringSplit
from spe.pipeline.operators.base.operators.transform.toFloat import ToFloat
from spe.pipeline.operators.base.operators.transform.toInt import ToInt
from spe.pipeline.operators.base.operators.transform.toString import ToString
from spe.pipeline.operators.base.operators.udf import UDF
from spe.pipeline.operators.base.operators.udo import UDO
from spe.pipeline.operators.base.operators.windows.tumblingWindowCount import TumblingWindowCount
from spe.pipeline.operators.base.operators.windows.tumblingWindowTime import TumblingWindowTime
from spe.pipeline.operators.base.operators.windows.windowCollect import WindowCollect
from spe.pipeline.operators.base.sources.httpGet import HTTPGet
from spe.pipeline.operators.base.sources.readFolder import ReadFolder
from spe.pipeline.operators.base.sources.socketServer import SocketServer
from spe.pipeline.operators.base.sources.textfile import TextFile
from spe.pipeline.operators.base.sources.uds import UDS
from spe.pipeline.operators.module import Module, MonitorDataType
from spe.runtime.monitor.dataInspect import DataInspect


class DictInspect(DataInspect):
    def getData(self, data):
        if self.inspectData is None:
            return data

        current = data

        for i in range(len(self.inspectData)):
            el = self.inspectData[i]

            if isinstance(el, list):
                current = current[el[0]]
            else:
                current = current[el]

        return current

    def _selectInternal(self, selected):
        if selected is None or selected == "":
            self.inspectData = None
        else:
            sp = selected.split(">")

            for i in range(len(sp)):
                val = sp[i]

                if val.startswith("[") and val.endswith("]"):
                    sp[i] = [int(val[1:len(val) - 1])]

            self.inspectData = sp

    def _getStructureInternal(self, data) -> json:
        keys = self._get_keys(data, {})

        return json.dumps(keys)

    def _get_keys(self, dl, keyDic):
        if isinstance(dl, dict):

            for key in dl.keys():
                d = self._get_keys(dl[key], {})

                if d is None:
                    d = type(dl[key]).__name__

                keyDic[key] = d

            return keyDic
        elif isinstance(dl, list):
            arr = []

            for v in dl:
                d = self._get_keys(v, {})

                if d is None:
                    d = type(v).__name__

                arr.append(d)

            return arr


class BaseModule(Module):
    def __init__(self):
        super(BaseModule, self).__init__("Base")

    def initialize(self):
        self.registerOp(ToInt, "Operators/Transform/ToInt")
        self.registerOp(ToFloat, "Operators/Transform/ToFloat")
        self.registerOp(ToString, "Operators/Transform/ToString")
        self.registerOp(StringSplit, "Operators/Transform/StringSplit")
        self.registerOp(Combine, "Operators/Transform/Combine")
        self.registerOp(ParseJSON, "Operators/Transform/ParseJSON")
        self.registerOp(FlattenList, "Operators/Transform/FlattenList")

        self.registerOp(Filter, "Operators/Filter")
        self.registerOp(UDF, "Operators/UDF")
        self.registerOp(UDS, "Sources/UDS")
        self.registerOp(UDO, "Operators/UDO")

        self.registerOp(TextFile, "Sources/TextFile")
        self.registerOp(HTTPGet, "Sources/HTTPGet")
        self.registerOp(ReadFolder, "Sources/ReadFolder")
        self.registerOp(SocketServer, "Sources/SocketServer")

        self.registerOp(TumblingWindowCount, "Operators/Windows/TumblingWindowCount")
        self.registerOp(TumblingWindowTime, "Operators/Windows/TumblingWindowTime")
        self.registerOp(WindowCollect, "Operators/Windows/WindowCollect")

        numberDT = MonitorDataType("NUMBER", lambda x: isinstance(x, numbers.Number))
        numberDT.registerDisplayMode(0, lambda x, y: round(x, 6))  # Raw value (max 6 digits)
        numberDT.registerDisplayMode(1, lambda x, y: ScatterplotD.fromElement(x))  # Timeline -> handled by client
        self.registerMonitorDataType(numberDT)

        strDT = MonitorDataType("STRING", lambda x: isinstance(x, str))  # Raw value
        strDT.registerDisplayMode(0, lambda x, y: x)
        strDT.registerDisplayMode(1, lambda x, y: len(x))
        self.registerMonitorDataType(strDT)

        numberArrayDT = MonitorDataType("ARRAY_NUMBER", lambda x: MonitorDataType.isArrayOf(x, numbers.Number, True))
        numberArrayDT.registerDisplayMode(0, lambda x, y: len(x))  # Count
        numberArrayDT.registerDisplayMode(1, lambda x, y: ScatterplotD.fromElements(x))  # Time-Series
        self.registerMonitorDataType(numberArrayDT)

        numberWindowDT = MonitorDataType("WINDOW_NUMBER", lambda x: MonitorDataType.isWindowOf(x, numbers.Number))
        numberWindowDT.registerDisplayMode(0, lambda x, y: x.getCount())  # Count
        numberWindowDT.registerDisplayMode(1, lambda x, y: ScatterplotD.fromElements(BaseModule.numberWindowToTimeSeries(x, y)))
        self.registerMonitorDataType(numberWindowDT)

        figureDT = MonitorDataType("FIGURE", lambda x: isinstance(x, FigureD))
        figureDT.registerDisplayMode(0, lambda x, y: x)
        self.registerMonitorDataType(figureDT)
        self.registerJSONEncoder(FigureD, lambda x: x.toDict())

        dictDT = MonitorDataType("DICT", lambda x: isinstance(x, dict))
        dictDT.registerInspect(DictInspect)
        self.registerMonitorDataType(dictDT)

    @staticmethod
    def numberWindowToTimeSeries(window, settings):
        data = []

        for t in range(0, window.getCount()):
            d = window.getDataAt(t)
            tup = window.getTupleAt(t)

            data.append([tup.eventTime, d])

        return data
