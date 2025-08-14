import json
import numbers

from spe.pipeline.operators.base.dataTypes.scatterplotD import ScatterplotD
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
        return None


class BaseModule(Module):
    def __init__(self):
        super(BaseModule, self).__init__("Base")

    def initialize(self):
        self.registerOp("spe.pipeline.operators.base.operators.transform.toInt", "ToInt", "Operators/Transform/ToInt")
        self.registerOp("spe.pipeline.operators.base.operators.transform.toBool", "ToBool", "Operators/Transform/ToBool")
        self.registerOp("spe.pipeline.operators.base.operators.transform.toFloat", "ToFloat", "Operators/Transform/ToFloat")
        self.registerOp("spe.pipeline.operators.base.operators.transform.toString", "ToString", "Operators/Transform/ToString")
        self.registerOp("spe.pipeline.operators.base.operators.transform.stringSplit", "StringSplit", "Operators/Transform/StringSplit")
        self.registerOp("spe.pipeline.operators.base.operators.transform.combine", "Combine", "Operators/Transform/Combine")
        self.registerOp("spe.pipeline.operators.base.operators.transform.parseJSON", "ParseJSON", "Operators/Transform/ParseJSON")
        self.registerOp("spe.pipeline.operators.base.operators.transform.serializeJSON", "SerializeJSON", "Operators/Transform/SerializeJSON")

        self.registerOp("spe.pipeline.operators.base.operators.filter", "Filter", "Operators/Filter")
        self.registerOp("spe.pipeline.operators.base.operators.udf", "UDF", "Operators/UDF")
        self.registerOp("spe.pipeline.operators.base.sources.uds", "UDS", "Sources/UDS")
        self.registerOp("spe.pipeline.operators.base.operators.udo", "UDO", "Operators/UDO")

        self.registerOp("spe.pipeline.operators.base.sources.textfile", "TextFile", "Sources/TextFile")
        self.registerOp("spe.pipeline.operators.base.sources.httpGet", "HTTPGet", "Sources/HTTPGet")
        self.registerOp("spe.pipeline.operators.base.sources.readFolder", "ReadFolder", "Sources/ReadFolder")
        self.registerOp("spe.pipeline.operators.base.sources.randomData", "RandomData", "Sources/RandomData")
        self.registerOp("spe.pipeline.operators.base.sources.socketServer", "SocketServer", "Sources/SocketServer")
        self.registerOp("spe.pipeline.operators.base.sources.socketTextSSource", "SocketTextSSource", "Sources/SocketTextSSource")
        self.registerOp("spe.pipeline.operators.base.sinks.socketTextSSink", "SocketTextSSink", "Sinks/SocketTextSSink")
        self.registerOp("spe.pipeline.operators.base.sources.kafkaSource", "KafkaSource", "Sources/KafkaSource")
        self.registerOp("spe.pipeline.operators.base.sinks.kafkaSink", "KafkaSink", "Sinks/KafkaSink")
        self.registerOp("spe.pipeline.operators.base.sinks.fileSink", "FileSink", "Sinks/FileSink")

        self.registerOp("spe.pipeline.operators.base.operators.windows.tumblingWindowCount", "TumblingWindowCount", "Operators/Windows/TumblingWindowCount")
        self.registerOp("spe.pipeline.operators.base.operators.windows.tumblingWindowTime", "TumblingWindowTime", "Operators/Windows/TumblingWindowTime")
        self.registerOp("spe.pipeline.operators.base.operators.windows.windowCollect", "WindowCollect", "Operators/Windows/WindowCollect")

        numberDT = MonitorDataType("NUMBER", lambda x: isinstance(x, numbers.Number))
        numberDT.registerDisplayMode(0, lambda x, y: round(x, 6))  # Raw value (max 6 digits)
        numberDT.registerDisplayMode(1, lambda x, y: ScatterplotD.fromElement(x))  # Timeline -> handled by client
        self.registerMonitorDataType(numberDT)

        strDT = MonitorDataType("STRING", lambda x: isinstance(x, str))  # Raw value
        strDT.registerDisplayMode(0, lambda x, y: x)
        strDT.registerDisplayMode(1, lambda x, y: len(x))
        self.registerMonitorDataType(strDT)

        numberArrayDT = MonitorDataType("ARRAY_NUMBER", lambda x: MonitorDataType.isArrayOf(x, numbers.Number, True, True))
        numberArrayDT.registerDisplayMode(0, lambda x, y: len(x))  # Count
        numberArrayDT.registerDisplayMode(1, lambda x, y: ScatterplotD.fromElements(x))  # Time-Series
        self.registerMonitorDataType(numberArrayDT)

        numberWindowDT = MonitorDataType("WINDOW_NUMBER", lambda x: MonitorDataType.isWindowOf(x, numbers.Number))
        numberWindowDT.registerDisplayMode(0, lambda x, y: x.getCount())  # Count
        numberWindowDT.registerDisplayMode(1, lambda x, y: ScatterplotD.fromElements(BaseModule.numberWindowToTimeSeries(x, y)))
        self.registerMonitorDataType(numberWindowDT)

        objectDT = MonitorDataType("OBJECT_INSPECT", lambda x: isinstance(x, dict) or isinstance(x, list))
        objectDT.registerInspect(DictInspect)
        self.registerMonitorDataType(objectDT)

    @staticmethod
    def numberWindowToTimeSeries(window, settings):
        data = []

        for t in range(0, window.getCount()):
            d = window.getDataAt(t)
            tup = window.getTupleAt(t)

            data.append([tup.eventTime, d])

        return data
