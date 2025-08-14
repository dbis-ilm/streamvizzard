from __future__ import annotations

import json
import logging
import os
import statistics
import traceback
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from spe.common.dataType import DataType
from spe.common.serialization.jsonSerialization import serializeToJSON, deserializeFromJSON
from spe.common.timer import Timer
from streamVizzard import StreamVizzard

if TYPE_CHECKING:
    from spe.pipeline.pipeline import Pipeline
    from spe.common.tuple import Tuple


class PipelineDataAnalyzer:
    def __init__(self):
        self._trackData = True

        self._opData: Dict[int, List[PipelineDataAnalyzer.TrackedData]] = dict()

        self._opInDataLookup: Dict[int, tuple[float, float, float]] = dict()

        self._hookedListeners = False

    def isTracking(self):
        return self._trackData

    def initialize(self, pipeline: Pipeline):
        if not self._trackData:
            return

        # This does not consider traversing of the history during debugging and tracks all processed tuples!

        for op in pipeline.getAllOperators():
            op.registerEvent(op.EVENT_TUPLE_PRE_PROCESSED, self._preTupleProcessed)
            op.registerEvent(op.EVENT_TUPLE_PROCESSED, self._onTupleProcessed)

        self._hookedListeners = True

    def changeConfig(self, trackData: bool, pipeline: Pipeline):
        self._trackData = trackData

        if not trackData:
            self._opData.clear()
            self._opInDataLookup.clear()
        elif not self._hookedListeners:
            self.initialize(pipeline)

    def finalize(self, pipeline: Pipeline):
        if not self._trackData:
            return

        # Aggregate and store data for each operator

        path = StreamVizzard.requestOutFolder("execution", "analysis")

        for opID, entries in self._opData.items():
            op = pipeline.getOperator(opID)

            if op is None:
                continue  # Delete

            exTimes = [entry.avgExTime for entry in entries]
            outDataSizes = [entry.avgOutDataSize for entry in entries]
            inDataSizes = [entry.avgInDataSize for entry in entries]
            outTps = [entry.avgOutThroughput for entry in entries]
            outDataSers = [entry.outDataSerialization for entry in entries]
            outDataDeSers = [entry.outDataDeserialization for entry in entries]
            inDataSers = [entry.inDataSerialization for entry in entries]
            inDataDeSers = [entry.inDataDeserialization for entry in entries]

            # For tps we take the minimum value of the inputs since this determines the actual input for this operator
            minTpVals = [min(e.avgInThroughput) for e in entries if len(e.avgInThroughput) > 0]

            # DataTypes

            inDataTypes = OperatorDataAnalysis.DataTypeEntry(len(op.inputs))
            outDataTypes = OperatorDataAnalysis.DataTypeEntry(len(op.outputs))

            for entry in entries:
                inDataTypes.registerOccurrence(entry.inDataTypes)
                outDataTypes.registerOccurrence(entry.outDataTypes)

            opEntry = OperatorDataAnalysis(opID, op.uuid, pipeline.uuid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                           len(entries), self._calculateStatistics(minTpVals),
                                           self._calculateStatistics(outTps),
                                           self._calculateStatistics(exTimes),
                                           self._calculateStatistics(outDataSizes),
                                           self._calculateStatistics(inDataSizes),
                                           outDataTypes, inDataTypes,
                                           self._calculateStatistics(outDataSers),
                                           self._calculateStatistics(outDataDeSers),
                                           self._calculateStatistics(inDataSers),
                                           self._calculateStatistics(inDataDeSers)
                                           )

            try:
                with open(os.path.join(path, f"opExStats_{op.uuid}.json"), "w") as f:
                    f.write(json.dumps(opEntry.toJSON()))
            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())

    @staticmethod
    def loadOperatorData(opUUID: str) -> Optional[OperatorDataAnalysis]:
        path = StreamVizzard.requestOutFolder("execution", "analysis")

        try:
            with open(os.path.join(path, f"opExStats_{opUUID}.json"), "r") as f:
                return OperatorDataAnalysis.fromJSON(json.load(f))
        except Exception:
            return None

    @staticmethod
    def _calculateStatistics(data: List[float]) -> OperatorDataAnalysis.StatsEntry:
        dataLength = len(data)

        median = statistics.median(data) if dataLength > 0 else 0
        average = statistics.mean(data) if dataLength > 0 else 0
        minimum = min(data) if dataLength > 0 else 0
        maximum = max(data) if dataLength > 0 else 0
        stdDev = statistics.stdev(data) if dataLength > 1 else 0

        return OperatorDataAnalysis.StatsEntry(median, average, minimum, maximum, stdDev)

    def _preTupleProcessed(self, tup: Tuple):
        if not self._trackData:
            return

        # Track the actual size / serialization time of the input data for this operator

        inDataSize = tup.calcMemorySize()

        inDataSerialization = 0
        inDataDeserialization = 0

        try:
            start = Timer.currentRealTime()
            ser = serializeToJSON(tup.data)
            end = Timer.currentRealTime()

            inDataSerialization = end - start

            start = Timer.currentRealTime()
            deserializeFromJSON(ser)
            end = Timer.currentRealTime()

            inDataDeserialization = end - start
        except Exception:
            pass  # Serialization/Deserialization not supported

        self._opInDataLookup[tup.operator.id] = (inDataSize, inDataSerialization, inDataDeserialization)

    def _onTupleProcessed(self, tup: Tuple, exTime: float):
        if not self._trackData:
            return

        op = tup.operator
        monitor = op.getMonitor()

        trackedList = self._opData.get(op.id)

        if trackedList is None:
            trackedList = []

            self._opData[op.id] = trackedList

        # IN Throughput

        inTps: List[float] = []

        for inp in op.inputs:
            for con in inp.getConnections():
                inTps.append(con.getMonitor().throughput)

        # IN DataSize

        inDataSize, inDataSer, inDataDeser = self._opInDataLookup.get(tup.operator.id, (0, 0, 0))  # Sources do not have input data

        # IN DataTypes

        inDataTypes: List[DataType] = []

        # Extract data types of the in tuple from the prev operators [low effort] -> Might be slightly inaccurate

        for inCon in op.getConnections(True, False):
            otherOp = inCon.output.op
            otherOpEntry = self._opData[otherOp.id][-1]

            inDataTypes.append(otherOpEntry.outDataTypes[inCon.output.id])

        # OUT Throughput

        outTp = 0

        for outP in op.outputs:
            for con in outP.getConnections():
                # Should be same for all OUT connections -> take max val
                outTp = max(con.getMonitor().throughput, outTp)

        # OUT DataSize

        outDataSize = monitor.getAvgDataSize()

        # OUT DataTypes -> High computation overhead if we check for uniformity

        outDataTypes: List[DataType] = [DataType.retrieve(d, True) for d in tup.data]

        # OUT Data Serialization

        outDataSerialization = 0
        outDataDeserialization = 0

        try:
            start = Timer.currentRealTime()
            ser = serializeToJSON(tup.data)
            end = Timer.currentRealTime()

            outDataSerialization = end - start

            start = Timer.currentRealTime()
            deserializeFromJSON(ser)
            end = Timer.currentRealTime()

            outDataDeserialization = end - start
        except Exception:
            pass  # Serialization/Deserialization not supported

        # Execution Time
        # Sources do not have execution times, their execution times is dependent on the input rate.

        # avgExTime = monitor.getAvgExecutionTime() / 1000 if not op.isSource() else 0
        avgExTime = exTime if not op.isSource() else 0

        # Register Data

        trackedList.append(PipelineDataAnalyzer.TrackedData(avgExTime,
                                                            outDataSize, inDataSize, tuple(inTps),
                                                            outTp, tuple(outDataTypes), tuple(inDataTypes),
                                                            outDataSerialization, outDataDeserialization,
                                                            inDataSer, inDataDeser))

    class TrackedData:
        def __init__(self, avgExTime: float, avgOutDataSize: float, avgInDataSize: float,
                     avgInThroughput: tuple[float, ...], avgOutThroughput: float,
                     outDataTypes: tuple[DataType, ...], inDataTypes: tuple[DataType, ...],
                     outDataSerialization: float, outDataDeserialization: float,
                     inDataSerialization: float, inDataDeserialization: float):
            self.avgExTime = avgExTime
            self.avgOutDataSize = avgOutDataSize
            self.avgInDataSize = avgInDataSize
            self.avgInThroughput = avgInThroughput
            self.avgOutThroughput = avgOutThroughput
            self.outDataTypes = outDataTypes
            self.inDataTypes = inDataTypes
            self.outDataSerialization = outDataSerialization
            self.outDataDeserialization = outDataDeserialization
            self.inDataSerialization = inDataSerialization
            self.inDataDeserialization = inDataDeserialization


class OperatorDataAnalysis:
    def __init__(self, opID: int, opUUID: str, pipelineUUID: str, timestamp: str,
                 totalTuples: int, inTpStats: StatsEntry, outTpStats: StatsEntry,
                 exTimeStats: StatsEntry,
                 outDataSizeStats: StatsEntry, inDataSizeStats: StatsEntry,
                 outDataTypes: DataTypeEntry, inDataTypes: DataTypeEntry,
                 outDataSerialization: StatsEntry, outDataDeserialization: StatsEntry,
                 inDataSerialization: StatsEntry, inDataDeserialization: StatsEntry):
        # General

        self.opID = opID
        self.opUUID = opUUID
        self.pipelineUUID = pipelineUUID
        self.timestamp = timestamp

        # Data

        self.totalTuples = totalTuples
        self.inTpStats = inTpStats  # tup/s
        self.outTpStats = outTpStats  # tup/s
        # This does include the overhead of StreamVizzard to schedule the operator execution.
        self.exTimeStats = exTimeStats  # s
        self.outDataSizeStats = outDataSizeStats  # [bytes] | Full output data size across all sockets
        self.inDataSizeStats = inDataSizeStats  # [bytes] | Actual received data size (socket dependent)

        self.outDataSerialization = outDataSerialization
        self.outDataDeserialization = outDataDeserialization
        self.inDataSerialization = inDataSerialization
        self.inDataDeserialization = inDataDeserialization

        self.outDataTypes = outDataTypes
        self.inDataTypes = inDataTypes

    def clone(self) -> OperatorDataAnalysis:
        return OperatorDataAnalysis.fromJSON(self.toJSON())

    def toJSON(self):
        return {"opID": self.opID, "opUUID": self.opUUID, "pipelineUUID": self.pipelineUUID, "timestamp": self.timestamp,
                "totalTuples": self.totalTuples, "inTpStats": self.inTpStats.toJSON(), "outTpStats": self.outTpStats.toJSON(),
                "exTimeStats": self.exTimeStats.toJSON(), "outDataSizeStats": self.outDataSizeStats.toJSON(),
                "inDataSizeStats": self.inDataSizeStats.toJSON(),
                "outDataTypes": self.outDataTypes.toJSON(), "inDataTypes": self.inDataTypes.toJSON(),
                "outDataSerialization": self.outDataSerialization.toJSON(), "outDataDeserialization": self.outDataDeserialization.toJSON(),
                "inDataSerialization": self.inDataSerialization.toJSON(), "inDataDeserialization": self.inDataDeserialization.toJSON()}

    @staticmethod
    def fromJSON(data: Dict) -> OperatorDataAnalysis:
        return OperatorDataAnalysis(data["opID"], data["opUUID"], data["pipelineUUID"], data["timestamp"], data["totalTuples"],
                                    OperatorDataAnalysis.StatsEntry.fromJSON(data["inTpStats"]),
                                    OperatorDataAnalysis.StatsEntry.fromJSON(data["outTpStats"]),
                                    OperatorDataAnalysis.StatsEntry.fromJSON(data["exTimeStats"]),
                                    OperatorDataAnalysis.StatsEntry.fromJSON(data["outDataSizeStats"]),
                                    OperatorDataAnalysis.StatsEntry.fromJSON(data["inDataSizeStats"]),
                                    OperatorDataAnalysis.DataTypeEntry.fromJSON(data["outDataTypes"]),
                                    OperatorDataAnalysis.DataTypeEntry.fromJSON(data["inDataTypes"]),
                                    OperatorDataAnalysis.StatsEntry.fromJSON(data["outDataSerialization"]),
                                    OperatorDataAnalysis.StatsEntry.fromJSON(data["outDataDeserialization"]),
                                    OperatorDataAnalysis.StatsEntry.fromJSON(data["inDataSerialization"]),
                                    OperatorDataAnalysis.StatsEntry.fromJSON(data["inDataDeserialization"])
                                    )

    class StatsEntry:
        def __init__(self, median: float, average: float, minVal: float, maxVal: float, std: float):
            self.median = median
            self.average = average
            self.min = minVal
            self.max = maxVal
            self.std = std

        def toJSON(self):
            return {"median": self.median, "average": self.average, "min": self.min, "max": self.max, "std": self.std}

        @staticmethod
        def fromJSON(data: Dict) -> OperatorDataAnalysis.StatsEntry:
            return OperatorDataAnalysis.StatsEntry(data["median"], data["average"], data["min"], data["max"], data["std"])

    class DataTypeEntry:
        class SocketData:
            def __init__(self):
                self.occurredTypes: List[DataType] = list()

                # Tracks which dataTypes (by name) are already registered
                self._dtNameLookup: Dict[str, List[DataType]] = dict()

            def isUniform(self) -> bool:
                # Only one data type was processed and that data type is uniform
                return len(self.occurredTypes) == 1 and self.occurredTypes[0].uniform

            def getUniformType(self) -> Optional[DataType]:
                return self.occurredTypes[0] if self.isUniform() else None

            def registerOccurrence(self, dt: DataType):
                if dt is None:
                    return

                prev = self._dtNameLookup.get(dt.typeName, [])

                for p in prev:
                    if p.isEquals(dt):  # Same dt (deep check)
                        return

                self.occurredTypes.append(dt)

                prev.append(dt)
                self._dtNameLookup[dt.typeName] = prev

            def toJSON(self) -> Dict:
                return {"occurrences": [t.toJSONConfig() for t in self.occurredTypes]}

            @staticmethod
            def fromJSON(data: Dict):
                sd = OperatorDataAnalysis.DataTypeEntry.SocketData()

                for ocData in data["occurrences"]:
                    sd.registerOccurrence(DataType.fromJSONConfig(ocData))

                return sd

        def __init__(self, socketCount: int):
            self._socketData = tuple([OperatorDataAnalysis.DataTypeEntry.SocketData() for _ in range(socketCount)])

        def getSocketData(self, sockID: int) -> SocketData:
            return self._socketData[sockID]

        def registerOccurrence(self, types: tuple[DataType, ...]):
            for socketID in range(min(len(types), len(self._socketData))):
                sockType: DataType = types[socketID]

                self._socketData[socketID].registerOccurrence(sockType)

        def toJSON(self) -> Dict:
            return {"socketData": [t.toJSON() for t in self._socketData]}

        @staticmethod
        def fromJSON(data: Dict) -> OperatorDataAnalysis.DataTypeEntry:
            socketData = data["socketData"]

            d = OperatorDataAnalysis.DataTypeEntry(len(socketData))

            socketDataList = [OperatorDataAnalysis.DataTypeEntry.SocketData.fromJSON(sd) for sd in socketData]

            d._socketData = tuple(socketDataList)

            return d
