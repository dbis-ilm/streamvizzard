from __future__ import annotations
from typing import Dict, Optional, TYPE_CHECKING, Set

from spe.pipeline.operators.base.operators.windows.windowOperator import WindowOperator
from spe.pipeline.pipeline import Pipeline
from spe.runtime.compiler.compilerRes import CompilerRes
from spe.runtime.compiler.codegeneration.codeGenerator import CodeGenerator
from spe.runtime.compiler.compileClustering import CompileClustering
from spe.runtime.compiler.compileDB import CompileDB
from spe.runtime.compiler.placement.knowledgeProvider.executionStatsKP import ExecutionStatsKP
from spe.runtime.compiler.placement.knowledgeProvider.opKnowledgeProvider import OpKnowledgeType
from spe.runtime.compiler.placement.strategies.placementStrategy import PlacementStrategy
from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from spe.runtime.compiler.opCompileData import OpCompileData

from spe.common.runtimeService import RuntimeService

if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from network.server import ServerManager


class PipelineCompiler(RuntimeService):
    def __init__(self, runtimeManager: RuntimeManager, serverManager: ServerManager):
        super().__init__(runtimeManager, serverManager)

        self.pipeline: Optional[Pipeline] = None
        self.compileDB: Optional[CompileDB] = None

    def reset(self):
        self.compileDB = None
        self.pipeline = None

    def onPipelineStarting(self):
        self.reset()  # Reset when a pipeline starts

    def onRuntimeShutdown(self):
        self.reset()  # Resets when runtime is shutdown

    def startCompileMode(self, pipeline: Pipeline):
        if self.isPipelineRunning():
            return

        self.reset()

        self.pipeline = pipeline

        # Initialize compile DB and specs

        if self.compileDB is None:
            self._initializeDB()

    def endCompileMode(self):
        self.reset()

    def calculateTargetSuggestions(self, strategyData: Dict, compileConfigs: Dict[str, Dict]) -> Optional[Dict]:
        if self.pipeline is None or self.isPipelineRunning():
            return None

        if not self._applyConfigurations(compileConfigs, True, True, True):
            return self._collectSuggestionResult()

        # Calculate suggestions for the user

        placementRes = self._applyPlacementStrategy(strategyData)

        if placementRes.hasError():
            return self._collectSuggestionResult()

        # Can only cluster, if every operator has a target

        if not self._verifyAllConfigs(False, True):
            return self._collectSuggestionResult()

        # Check out-of-order processing

        self._detectOutOfOrderOccurrences()

        # Cluster the targets

        self._calculateCluster()

        return self._collectSuggestionResult(placementRes.statusMsg)

    def _applyConfigurations(self, compileConfigs: Dict[str, Dict], allowEmptyTargets: bool,
                             allowEmptyClusters: bool, resetAuto: bool) -> bool:
        # First, apply all provided configs to the ops

        for op in self.pipeline.getAllOperators():
            compileData = self.compileDB.opCompileData[op.id]

            preset = compileConfigs.get(str(op.id), None)

            if preset is None:  # No preset was provided
                compileData.compileConfig.reset()
            else:  # Take provided values - reset target if auto
                compileData.compileConfig = OpCompileConfig.fromJSON(preset)

                if not compileData.compileConfig.manual and resetAuto:
                    compileData.compileConfig.resetTarget()

        # Then, check if they are valid

        return self._verifyAllConfigs(allowEmptyTargets, allowEmptyClusters)

    def _verifyAllConfigs(self, allowEmptyTargets: bool, allowEmptyClusters: bool) -> bool:
        # Analyze and validate all configs of the operators, including clusters

        res = True

        for op in self.pipeline.getAllOperators():
            compileData = self.compileDB.opCompileData[op.id]

            # Verify target & cluster

            if not compileData.verifyTarget() and not allowEmptyTargets:
                res = False

            # Not supporting compilation always forces a failure!

            if not compileData.supportsCompilation():
                res = False

            if not compileData.verifyCluster(self.compileDB) and not allowEmptyClusters:
                res = False

        return res

    def _collectSuggestionResult(self, statusMsg: Optional[str] = None) -> Optional[Dict]:
        errorMsg: Set[str] = set()
        res = []

        for op in self.pipeline.getAllOperators():
            data = self.compileDB.opCompileData[op.id]

            fws = []
            ccs = []
            cfg = data.compileConfig
            estimatedTargetStats = None

            op.clearExecutionError()  # Reset error

            if not data.supportsCompilation():
                op.onExecutionError("Operator doesn't support compilation!")
                errorMsg.add("Compilation not supported for this pipeline!")
            else:
                fws = data.specsCatalog.deriveEnvRules()

                if not cfg.hasValidTarget():
                    op.onExecutionError("Couldn't find a suitable compilation target!")
                    errorMsg.add("Couldn't calculate compilation targets!")

                if data.estimatedTargetStats is not None:
                    estimatedTargetStats = data.estimatedTargetStats.toJSON()

                if cfg.cluster is not None:
                    cluster = self.compileDB.cluster[cfg.cluster.clusterID]

                    for cc in cluster.clusterConnections:
                        if not cc.hasCompatible():
                            op.onExecutionError("No compatible connectors for connection " + str(cc.connection.id) + " to other cluster!")

                            errorMsg.add("Couldn't connect the compilation targets!")

                    ccs = cluster.exportSupportedConnections(op)

            # Check if this operator has available execution stats
            exStats: ExecutionStatsKP = data.getKnowledgeProvider(OpKnowledgeType.EXECUTION_STATS)

            res.append({"opID": op.id,
                        "res": {
                            "frameworks": fws,
                            "clusterConnections": ccs,
                            "targetStatsEstimation": estimatedTargetStats,
                            "config": cfg.toJSON() if cfg.hasValidTarget() else None,
                            "meta": data.metaData.toJSON()
                        },
                        "status": {
                            "exStatsAvail": exStats.getStats() is not None}
                        })

        hasError = len(errorMsg) > 0

        return {"error": "\n".join(errorMsg) if hasError else None, "statusMsg": statusMsg,
                "opData": res, "canCompile": not hasError}

    def compilePipeline(self, opCompileConfigs: Dict[str, Dict], compileConfig: Dict) -> CompilerRes:
        if self.pipeline is None or self.isPipelineRunning():
            return CompilerRes("Invalid pipeline state!")

        if not self._applyConfigurations(opCompileConfigs, False, False, False):
            return CompilerRes("Couldn't apply operator target configurations!")

        # Reset all previous errors

        for op in self.pipeline.getAllOperators():
            op.clearExecutionError()

        codeGen = CodeGenerator(self.compileDB, self.pipeline, compileConfig["settings"])
        return codeGen.generate()

    def _initializeDB(self):
        self.compileDB = CompileDB()

        for op in self.pipeline.getAllOperators():
            compileData = OpCompileData(op)

            self.compileDB.opCompileData[op.id] = compileData

    def _applyPlacementStrategy(self, strategyConfig: Dict) -> CompilerRes:
        strategy = PlacementStrategy.get(strategyConfig["name"])

        if strategy is None:
            return CompilerRes.error(f"No placement strategy found for name {strategyConfig['name']}!")

        strategyInst = strategy(self.pipeline, self.compileDB, strategyConfig["settings"])

        return strategyInst.apply()

    def _calculateCluster(self):
        # Calculates a clustering of related operators, which is relevant for the subsequent code generation.

        cl = CompileClustering(self.compileDB, self.pipeline)
        cl.calculateCluster()

    def _detectOutOfOrderOccurrences(self):
        for opData in self.compileDB.opCompileData.values():
            # Reset
            opData.metaData.canRestoreOutOfOrder = False
            opData.metaData.outOfOrderProcessing = False
            opData.metaData.outOfOrderCause = None

            paraCount = opData.compileConfig.parallelismCount
            inNeighbours = opData.operator.getNeighbours(True, False)

            # --- SOURCE ---

            if opData.operator.isSource():
                # A source might produce data out-of-order if it has parallelism > 1
                # (This can't be fixed be reordering since we currently do not have event times in the data)

                if paraCount > 1:
                    opData.metaData.outOfOrderProcessing = True
                    opData.metaData.outOfOrderCause = OpCompileData.MetaData.OutOfOrderCause.SOURCE
                    opData.metaData.canRestoreOutOfOrder = False

            # --- JOIN ---

            elif len(inNeighbours) > 1:
                # A join operator combines result values out-of-order if the IN operators have different parallelisms than the join
                # Exception: If the join has parallelism=1 and uses reordering

                samePara = None

                for n in inNeighbours:
                    nData = self.compileDB.opCompileData[n.id]
                    nPara = nData.compileConfig.parallelismCount

                    if samePara is None:
                        samePara = nPara

                    if nPara != samePara or nPara != paraCount:
                        opData.metaData.outOfOrderProcessing = True
                        opData.metaData.outOfOrderCause = OpCompileData.MetaData.OutOfOrderCause.JOIN
                        opData.metaData.canRestoreOutOfOrder = True

                        if paraCount == 1 and opData.compileConfig.enforceTupleOrder:
                            opData.metaData.outOfOrderProcessing = False  # Resolved

                        break

            # --- WINDOW ---

            elif isinstance(opData.operator, WindowOperator):
                # Distributed window operators may lead to out-of-order, since values are potentially assigned
                # round-robin to the involved window partitions.
                # Exception: if all preceding operators (globally) have the same level of parallelism as the window

                if paraCount > 1:
                    globalIns = opData.operator.getGlobalNeighbours(True, False)

                    for gIn in globalIns:
                        inData = self.compileDB.opCompileData[gIn.id]

                        # Predecessor has different para -> out-of-order

                        if inData.compileConfig.parallelismCount != paraCount:
                            opData.metaData.outOfOrderProcessing = True
                            opData.metaData.outOfOrderCause = OpCompileData.MetaData.OutOfOrderCause.WINDOW
                            opData.metaData.canRestoreOutOfOrder = False

                            break

            # --- OTHER ---

            else:
                # An operator processes tuples out-of-order if at least on of its input operators has a higher parallelism count

                for n in inNeighbours:
                    nData = self.compileDB.opCompileData[n.id]

                    if nData.compileConfig.parallelismCount > paraCount:
                        opData.metaData.outOfOrderProcessing = True
                        opData.metaData.outOfOrderCause = OpCompileData.MetaData.OutOfOrderCause.INPUT_PARA
                        opData.metaData.canRestoreOutOfOrder = True

                        if opData.compileConfig.enforceTupleOrder:
                            opData.metaData.outOfOrderProcessing = False  # Resolved

                        break
