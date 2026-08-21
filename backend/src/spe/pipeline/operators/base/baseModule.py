from typing import Optional

from spe.common.dataType import FloatType, StringType, ArrayType, IntegerType, NoneType, DictType, TupleType
from spe.pipeline.operators.base.dataTypes.scatterplotD import ScatterplotD
from spe.pipeline.operators.module import Module
from spe.runtime.monitor.dataInspectType import DataInspectType
from spe.runtime.monitor.dataDisplayType import DataDisplayType
from spe.runtime.monitor.dataInspect import DataInspect


class ObjectInspect(DataInspect):
    """ Supports Tuple, List, Dict """

    def _getStructure(self, data, parentEntry: Optional[DataInspect.Entry] = None) -> DataInspect.Entry:
        """ Fetches all entries from this object (recursive) and returns the object as a root node with children """

        if isinstance(data, dict):
            if parentEntry is None:
                parentEntry = DataInspect.Entry.getRootEntry(dict.__name__)

            for key in data.keys():
                dataPortion = data[key]
                dataType = type(dataPortion).__name__

                newEntry = DataInspect.Entry(key, dataType, lambda name, d: d[name])  # Dict access (name=key)

                if not parentEntry.addChild(newEntry):
                    continue  # Size limit reached, stop following this entry

                self._getStructure(dataPortion, newEntry)  # Recursive
        elif isinstance(data, (list, tuple)):
            if parentEntry is None:
                parentEntry = DataInspect.Entry.getRootEntry(type(data).__name__)

            for v in range(len(data)):
                dataPortion = data[v]
                dataType = type(dataPortion).__name__

                newEntry = DataInspect.Entry(str(v), dataType, lambda name, d: d[int(name)])  # Array access (name=index)

                if not parentEntry.addChild(newEntry):
                    continue  # Size limit reached, stop following this entry

                self._getStructure(dataPortion, newEntry)  # Recursive

        return parentEntry


class BaseModule(Module):
    def __init__(self):
        super(BaseModule, self).__init__("Base")

    def initialize(self):
        self.registerOp("spe.pipeline.operators.base.operators.transform.cast", "Cast", "Operators/Transform/Cast")
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
        self.registerOp("spe.pipeline.operators.base.sources.textSocketServer", "TextSocketServer", "Sources/TextSocketServer")
        self.registerOp("spe.pipeline.operators.base.sinks.socketServer", "SocketServer", "Sinks/SocketServer")
        self.registerOp("spe.pipeline.operators.base.sinks.textSocketServer", "TextSocketServer", "Sinks/TextSocketServer")
        self.registerOp("spe.pipeline.operators.base.sources.kafkaSource", "KafkaSource", "Sources/KafkaSource")
        self.registerOp("spe.pipeline.operators.base.sinks.kafkaSink", "KafkaSink", "Sinks/KafkaSink")
        self.registerOp("spe.pipeline.operators.base.sinks.fileSink", "FileSink", "Sinks/FileSink")

        self.registerOp("spe.pipeline.operators.base.operators.windows.tumblingWindowCount", "TumblingWindowCount", "Operators/Windows/TumblingWindowCount")
        self.registerOp("spe.pipeline.operators.base.operators.windows.tumblingWindowTime", "TumblingWindowTime", "Operators/Windows/TumblingWindowTime")
        self.registerOp("spe.pipeline.operators.base.operators.windows.slidingWindowCount", "SlidingWindowCount", "Operators/Windows/SlidingWindowCount")
        self.registerOp("spe.pipeline.operators.base.operators.windows.slidingWindowTime", "SlidingWindowTime", "Operators/Windows/SlidingWindowTime")
        self.registerOp("spe.pipeline.operators.base.operators.windows.windowCollect", "WindowCollect", "Operators/Windows/WindowCollect")

        noneDT = DataDisplayType("NONE", [DataDisplayType.TypeEntry(NoneType())])
        noneDT.registerDisplayMode(0, lambda x, y: x)  # Raw value
        self.registerMonitorDataType(noneDT)

        numberDT = DataDisplayType("NUMBER", [
            DataDisplayType.TypeEntry(FloatType()),
            DataDisplayType.TypeEntry(IntegerType())
        ])
        numberDT.registerDisplayMode(0, lambda x, y: round(x, 6))  # Raw value (max 6 digits)
        numberDT.registerDisplayMode(1, lambda x, y: ScatterplotD.fromElement(x, y))  # Timeline -> handled by client
        self.registerMonitorDataType(numberDT)

        strDT = DataDisplayType("STRING", [DataDisplayType.TypeEntry(StringType())])
        strDT.registerDisplayMode(0, lambda x, y: x)  # Raw value
        strDT.registerDisplayMode(1, lambda x, y: len(x))
        self.registerMonitorDataType(strDT)

        numberArrayDT = DataDisplayType("ARRAY_NUMBER", [
            DataDisplayType.TypeEntry(ArrayType(entryType=NoneType())),  # Array with None values
            DataDisplayType.TypeEntry(ArrayType(entryType=None)),  # Empty Array / Unknown types
            DataDisplayType.TypeEntry(ArrayType(entryType=IntegerType())),
            DataDisplayType.TypeEntry(ArrayType(entryType=FloatType()))
        ])
        numberArrayDT.registerDisplayMode(0, lambda x, y: len(x))  # Count
        numberArrayDT.registerDisplayMode(1, lambda x, y: ScatterplotD.fromElements(x, y))  # Time-Series
        self.registerMonitorDataType(numberArrayDT)

        objectDT = DataInspectType("DICT_INSPECT", [DataDisplayType.TypeEntry(DictType(), True)], ObjectInspect)
        self.registerMonitorDataType(objectDT)

        objectDT = DataInspectType("ARRAY_INSPECT", [DataDisplayType.TypeEntry(ArrayType(), True)], ObjectInspect)
        self.registerMonitorDataType(objectDT)

        objectDT = DataInspectType("TUPLE_INSPECT", [DataDisplayType.TypeEntry(TupleType(), True)], ObjectInspect)
        self.registerMonitorDataType(objectDT)
