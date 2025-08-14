from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Set, Optional

from spe.common.serialization.serializationMode import SerializationMode
from spe.pipeline.operators.base.operators.windows.windowCollect import WindowCollect
from spe.common.dataType import DataType, WindowType, StringType, ArrayType
from spe.runtime.compiler.compilerRes import CompilerRes
from spe.runtime.compiler.definitions.compileDefinitions import CompileLanguage, CompileComputeMode, CompileParallelism, \
    CompileFramework, CompileFrameworkConnector
from spe.pipeline.connection import Connection
from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from spe.runtime.compiler.opCompileData import OpCompileData
from spe.runtime.compiler.placement.knowledgeProvider.opKnowledgeProvider import OpKnowledgeType
from spe.runtime.monitor.pipelineDataAnalyzer import OperatorDataAnalysis
from utils.utils import printWarning


if TYPE_CHECKING:
    from spe.pipeline.socket import Socket
    from spe.runtime.compiler.codegeneration.codeGenerator import CodeGenerator
    from spe.runtime.compiler.placement.knowledgeProvider.executionStatsKP import ExecutionStatsKP
    from spe.runtime.compiler.definitions.compileFrameworkSpecs import CompileFrameworkSpecs
    from spe.pipeline.operators.operator import Operator


class FrameworkCompiler(ABC):
    def __init__(self, framework: CompileFrameworkSpecs, clusterID: int, generator: CodeGenerator):
        self.generator = generator
        self.framework = framework
        self.clusterID = clusterID

        self.opNodes: List[OpCompileData] = []

        self._opIDs: Set[int] = set()
        self._conIDs: Set[int] = set()

    @abstractmethod
    def generateCode(self) -> CompilerRes:
        pass

    def registerOperator(self, op: OpCompileData):
        self.opNodes.append(op)

        self._registerOperatorIDs(op.operator)

    def _registerOperatorIDs(self, op: Operator):
        # Verify that we do not have duplicates in IDs

        if op.id in self._opIDs:
            op.id = self._generateNewOpID()

        self._opIDs.add(op.id)

        # Register IDs of all op connections [cons to ops outside our cluster are already removed]

        for i in op.inputs + op.outputs:
            for c in i.getConnections():
                # Make sure that we do not have duplicates in con IDs

                if c.id in self._conIDs:
                    c.id = self._generateNewConID()

                self._conIDs.add(c.id)

    @abstractmethod
    def registerConnector(self, cc: OpCompileConfig.ClusterConnectionConfig, con: Connection, socket: Socket) -> CompilerRes:
        pass

    @abstractmethod
    def mergeWith(self, otherCp: FrameworkCompiler) -> bool:
        pass

    def _generateNewOpID(self, regInSet: bool = False):
        currentMax = 0

        for opID in self._opIDs:
            currentMax = max(currentMax, opID)

        if regInSet:
            self._opIDs.add(currentMax + 1)

        return currentMax + 1

    def _generateNewConID(self, regInSet: bool = False) -> int:
        currentMax = 0

        for conID in self._conIDs:
            currentMax = max(currentMax, conID)

        if regInSet:
            self._conIDs.add(currentMax + 1)

        return currentMax + 1

    # --------------------------------------------------- Connectors ---------------------------------------------------

    def _generateKafkaConnector(self, cc: OpCompileConfig.ClusterConnectionConfig, socket: Socket, language: CompileLanguage) -> CompilerRes:
        rootOpData = self.generator.compileDB.opCompileData[socket.op.id]

        if socket.inSocket:
            from spe.pipeline.operators.base.sources.kafkaSource import KafkaSource

            kafkaConnector = KafkaSource(self._generateNewOpID())
            kafkaConnector.setData({"port": cc.params["port"], "broker": cc.params["broker"], "encoding": "utf-8",
                                    "topic": cc.params["topic"], "groupID": "conGroup", "offset": "latest"})

            return self._setupConnector(socket, kafkaConnector, None, StringType(),
                                        cc.conType, SerializationMode.JSON, language, rootOpData)
        else:
            from spe.pipeline.operators.base.sinks.kafkaSink import KafkaSink

            kafkaConnector = KafkaSink(self._generateNewOpID())
            kafkaConnector.setData({"port": cc.params["port"], "broker": cc.params["broker"],
                                    "encoding": "utf-8", "topic": cc.params["topic"],
                                    "maxRequestSize": kafkaConnector.maxRequestSize})

            return self._setupConnector(socket, kafkaConnector, StringType(), None,
                                        cc.conType, SerializationMode.JSON, language, rootOpData)

    def _setupConnector(self, socket: Socket, connectorOp: Operator, conInType: Optional[DataType], conOutType: Optional[DataType],
                        conType: CompileFrameworkConnector, serializationMode: SerializationMode,
                        language: CompileLanguage, rootOpData: OpCompileData) -> CompilerRes:

        # Find dataType this connector need to transfer

        kp: ExecutionStatsKP = rootOpData.getKnowledgeProvider(OpKnowledgeType.EXECUTION_STATS)
        stats = kp.getStats()

        conDataType: Optional[DataType] = None

        if stats is not None:
            sockData = stats.inDataTypes.getSocketData(socket.id) if socket.inSocket else stats.outDataTypes.getSocketData(socket.id)
            conDataType = sockData.getUniformType()

        # Find suitable parallelism of this connector

        maxConPara = self.framework.getConnectorConfig(conType, socket.inSocket).maxParallelism
        opPara = rootOpData.compileConfig.parallelismCount
        conParallelism = min(maxConPara, opPara) if maxConPara is not None else opPara

        # Find list of data transformer

        transformer = self._getConnectorDataDeserializer(serializationMode, conDataType) if socket.inSocket \
            else self._getConnectorDataSerializer(serializationMode, conDataType)

        if transformer is None or len(transformer) == 0:
            return CompilerRes(f"{'Deserialization' if socket.inSocket else 'Serialization'} for connection data of type '{conDataType.typeName}' not supported!")

        # Register actual connector

        self._registerConnectorOp(connectorOp, language, conParallelism, inDataType=conInType, outDataType=conOutType, rootOp=rootOpData)

        if socket.inSocket:  # Source Connector -> [Transformers]
            lastSock = connectorOp.getOutput(0)
            lastOutDT = conInType
            targetSock = socket  # Connect last transformer to actual pipeline op
        else:  # [Transformers] -> Sink Connector
            lastSock = socket
            lastOutDT = conDataType  # (The actual op of the pipeline)
            targetSock = connectorOp.getInput(0)  # Connect last transformer to connector op

        # Add transformer

        for idx, tr in enumerate(transformer):
            Connection.create(self._generateNewConID(), tr[0].getInput(0), lastSock)
            self._registerConnectorOp(tr[0], language, conParallelism, inDataType=lastOutDT, outDataType=tr[1], rootOp=rootOpData)

            lastSock = tr[0].getOutput(0)
            lastOutDT = tr[1]

        Connection.create(self._generateNewConID(), targetSock, lastSock)

        return CompilerRes.ok()

    def _registerConnectorOp(self, op: Operator, language: CompileLanguage, parallelism: int,
                             inDataType: Optional[DataType], outDataType: Optional[DataType], rootOp: OpCompileData):
        # Creates a dummy compile data and registers the artificial connector operator.
        # OpCompileData is required for the later code generation.
        # We assume, all connector operators have one input and one output

        dummyCfg = OpCompileConfig()
        dummyCfg.framework = self.framework.framework
        dummyCfg.language = language
        dummyCfg.computeMode = CompileComputeMode.CPU
        dummyCfg.parallelism = CompileParallelism.SINGLE_NODE if parallelism == 1 else CompileParallelism.DISTRIBUTED
        dummyCfg.parallelismCount = parallelism

        opData = OpCompileData(op)
        opData.compileConfig.setTarget(dummyCfg)

        # Clone execution stats of root operator (we create connection for) and adapt in / out types

        rootKp: ExecutionStatsKP = rootOp.getKnowledgeProvider(OpKnowledgeType.EXECUTION_STATS)
        rootStats = rootKp.getStats()

        kp: ExecutionStatsKP = opData.getKnowledgeProvider(OpKnowledgeType.EXECUTION_STATS)
        kp.operatorUUID = opData.operator.uuid
        kp.opStats = rootStats.clone() if rootStats is not None else None

        if kp.opStats is not None:
            kp.opStats.inDataTypes = OperatorDataAnalysis.DataTypeEntry(len(op.inputs))
            kp.opStats.outDataTypes = OperatorDataAnalysis.DataTypeEntry(len(op.outputs))

            if len(op.inputs) > 0:
                kp.opStats.inDataTypes.getSocketData(0).occurredTypes = [inDataType] if inDataType is not None else []
            if len(op.outputs) > 0:
                kp.opStats.outDataTypes.getSocketData(0).occurredTypes = [outDataType] if outDataType is not None else []

        self.registerOperator(opData)

    def _getConnectorDataSerializer(self, mode: SerializationMode, inType: DataType) -> List[tuple[Operator, DataType]]:
        # Returns a list of serializing operators and their respective output types

        transformerList: List[tuple[Operator, DataType]] = []

        if isinstance(inType, WindowType):  # Special case -> transform Window to DataArray first
            windowCollect = WindowCollect(self._generateNewOpID())

            transformerList.append((windowCollect, ArrayType(entryType=inType.entryType, uniform=True)))

        if mode == SerializationMode.JSON:
            from spe.pipeline.operators.base.operators.transform.serializeJSON import SerializeJSON
            serializeJSON = SerializeJSON(self._generateNewOpID())

            transformerList.append((serializeJSON, StringType()))

        return transformerList

    def _getConnectorDataDeserializer(self, mode: SerializationMode, outType: DataType) -> Optional[List[tuple[Operator, DataType]]]:
        # Returns a list of deserializing operators and their respective output types

        transformerList: List[tuple[Operator, DataType]] = []

        if mode == SerializationMode.JSON:
            from spe.pipeline.operators.base.operators.transform.parseJSON import ParseJSON
            parseJSON = ParseJSON(self._generateNewOpID())

            transformerList.append((parseJSON, outType))

        # Special case -> transform DataArray to Window again [if on SV]
        if isinstance(outType, WindowType) and self.framework.framework == CompileFramework.STREAMVIZZARD:
            printWarning("Deserializing back to Window operator on SV currently not supported!")

            return None

        return transformerList
