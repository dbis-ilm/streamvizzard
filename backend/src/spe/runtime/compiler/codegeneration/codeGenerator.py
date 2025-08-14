from __future__ import annotations

from typing import Dict, TYPE_CHECKING, Optional, List

from spe.runtime.compiler.compilerRes import CompilerRes
from spe.runtime.compiler.codegeneration.frameworks.frameworkCompiler import FrameworkCompiler
from spe.runtime.compiler.definitions.compileFrameworkSpecs import getSupportedFramework
from streamVizzard import StreamVizzard
from utils.fileUtils import emptyFolder

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.compiler.opCompileData import OpCompileData
    from spe.pipeline.connection import Connection
    from spe.pipeline.pipeline import Pipeline
    from spe.runtime.compiler.compileDB import CompileDB
    from spe.runtime.compiler.definitions.compileFrameworkSpecs import CompileFrameworkSpecs


class CodeGenerator:
    def __init__(self, compileDB: CompileDB, pipeline: Pipeline, config: Dict):
        self.compileDB = compileDB
        self.pipeline = pipeline

        self.frameworkCompiler: Dict[int, FrameworkCompiler] = dict()

        self._mergeCluster: bool = config["mergeCluster"]

        self._clusterConnections: Dict[int, Connection] = dict()

    def generate(self) -> CompilerRes:
        # Handle all operators and register them in their framework compiler

        for op in self.pipeline.getAllOperators():
            opData = self.compileDB.opCompileData[op.id]

            self._handleOperator(opData)

        # Create connections between cluster

        if not self._createClusterConnections():
            return self._finalizeGeneration(CompilerRes("Failed to create cluster connections!"))

        # Merge cluster together if possible (same framework) -> minimize overhead by the frameworks

        if self._mergeCluster and not self._tryClusterMerge():
            return self._finalizeGeneration(CompilerRes("Failed to merge clusters!"))

        # Generate the code

        emptyFolder(self.getOutputPath())

        for compiler in self.frameworkCompiler.values():
            genRes = compiler.generateCode()

            if genRes.hasError():
                return self._finalizeGeneration(genRes)

        return self._finalizeGeneration(CompilerRes.ok(self.getOutputPath()))

    def _finalizeGeneration(self, result: CompilerRes) -> CompilerRes:
        if result.hasError():
            emptyFolder(self.getOutputPath())  # Cleanup folders

        # Restore original ids of the operators which might have been modified during merge

        for opID, op in self.pipeline._operatorLookup.items():
            op.id = opID

        # Restore original connections of the pipeline, since we might have added/removed cluster connections

        for op in self.pipeline.getAllOperators():
            for socket in op.inputs + op.outputs:
                socket.clearConnections()

        for con in self.pipeline.getAllConnections():  # We assume, this lookup hasn't been modified
            con.input.addConnection(con)
            con.output.addConnection(con)

        return result

    def _handleOperator(self, opData: OpCompileData):
        # Registers the operator in the respective framework compiler
        # Also detects and registers connectors to operators of other clusters

        cp = self._getOrCreateFrameworkCompiler(opData)

        def handleNeighbour(other: Operator, connection: Connection) -> Optional[bool]:
            otherData = self.compileDB.opCompileData[other.id]

            if otherData.compileConfig.cluster.clusterID == opData.compileConfig.cluster.clusterID:
                return  # Same cluster, nothing to do

            # Drop old connection (to op of other cluster)

            socket.removeConnection(con)

            # Register cluster connection

            self._clusterConnections[connection.id] = connection

        # Handle inputs

        for socket in opData.operator.inputs:
            for con in socket.getConnections():
                handleNeighbour(con.output.op, con)

        # Handle outputs

        for socket in opData.operator.outputs:
            for con in socket.getConnections():
                handleNeighbour(con.input.op, con)

        cp.registerOperator(opData)

    def _createClusterConnections(self) -> bool:
        for con in self._clusterConnections.values():
            opDataSource = self.compileDB.opCompileData[con.input.op.id]
            opDataSink = self.compileDB.opCompileData[con.output.op.id]

            ccSource = opDataSource.compileConfig.cluster.getConnectionConfig(con.id)
            ccSink = opDataSink.compileConfig.cluster.getConnectionConfig(con.id)

            cpSource = self._getOrCreateFrameworkCompiler(opDataSource)
            cpSink = self._getOrCreateFrameworkCompiler(opDataSink)

            # Register connection in both framework compiler

            res = cpSource.registerConnector(ccSource, con, con.input)

            if res.hasError():
                opDataSource.operator.onExecutionError(res.errorMsg)

                return False

            res = cpSink.registerConnector(ccSink, con, con.output)

            if res.hasError():
                opDataSink.operator.onExecutionError(res.errorMsg)

                return False

            # Remove connections from original sockets

            con.input.removeConnection(con)
            con.output.removeConnection(con)

        return True

    def _tryClusterMerge(self) -> bool:
        mergeCandidates: Dict[CompileFrameworkSpecs, List[FrameworkCompiler]] = dict()

        for cp in self.frameworkCompiler.values():
            fwList = mergeCandidates.get(cp.framework)

            if fwList is None:
                fwList = []

            fwList.append(cp)

            mergeCandidates[cp.framework] = fwList

        for fw, cpEntries in mergeCandidates.items():
            if not fw.supportsMergedClusters:
                continue

            if len(cpEntries) < 2:
                continue

            first = cpEntries[0]

            for other in cpEntries:
                if other == first:
                    continue

                if not first.mergeWith(other):
                    return False

                self.frameworkCompiler.pop(other.clusterID)

        return True

    def _getOrCreateFrameworkCompiler(self, opData: OpCompileData) -> FrameworkCompiler:
        sCfg = opData.compileConfig

        framework = getSupportedFramework(sCfg.framework)

        fwCompiler = self.frameworkCompiler.get(sCfg.cluster.clusterID, None)

        if fwCompiler is None:
            fwCompiler = framework.compiler(framework, sCfg.cluster.clusterID, self)
            self.frameworkCompiler[sCfg.cluster.clusterID] = fwCompiler

        return fwCompiler

    @staticmethod
    def getOutputPath() -> str:
        return StreamVizzard.requestOutFolder("compilation")
