from __future__ import annotations
import abc
from typing import Dict, TYPE_CHECKING, Optional, Type

from spe.runtime.compiler.compilerRes import CompilerRes
from spe.runtime.compiler.placement.knowledgeProvider.executionStatsKP import ExecutionStatsKP
from spe.runtime.compiler.placement.knowledgeProvider.opKnowledgeProvider import OpKnowledgeType
from spe.runtime.compiler.placement.opTargetCatalog import OpTargetOption
from utils.utils import tryParseInt, tryParseFloat

if TYPE_CHECKING:
    from spe.runtime.compiler.compileDB import CompileDB
    from spe.runtime.compiler.opCompileData import OpCompileData
    from spe.pipeline.pipeline import Pipeline


class PlacementStrategy(abc.ABC):
    def __init__(self, pipeline: Pipeline, compileDB: CompileDB, config: Dict):
        self.pipeline = pipeline
        self.compileDB = compileDB
        self.config = config

        # General params provided for every strategy

        self.costModelPath: Optional[str] = config.get("costModelPath", None)
        self.maxNodesCount: Optional[int] = tryParseInt(config.get("maxNodesCount"), None)

        # Inter-Executor Stats
        self.avgNodeTransferSpeed = tryParseFloat(config.get("avgNodeTransferSpeed"), 100) * 1000000  # MB/s -> bytes/s
        self.avgNodeTransferLatency = tryParseFloat(config.get("avgNodeTransferLatency"), 0.25) / 1000  # ms -> s

        # Connector Stats | Future Work: Consider Connector-specific overheads
        self.avgConnectorTransferSpeed = tryParseFloat(config.get("avgConnectorTransferSpeed"), 100) * 1000000  # MB/s -> bytes/s
        self.avgConnectorTransferLatency = tryParseFloat(config.get("avgConnectorTransferLatency"), 10) / 1000  # ms

        self.avgGPUTransferSpeed = tryParseFloat(config.get("avgGPUTransferSpeed"), 10000) * 1000000  # MB/s
        self.avgGPULatency = tryParseFloat(config.get("avgGPULatency"), 0.1) / 1000  # ms

        self.targetSwitchPenalty = 1 / 1_000_000  # [s] Motivate algorithm to stick to same target if no stats are provided

        self._determineTargetTps()

        # Clear previous target result estimations

        for op in self.compileDB.opCompileData.values():
            op.estimatedTargetStats = None

    @abc.abstractmethod
    def apply(self) -> CompilerRes:
        ...

    @staticmethod
    def get(name: str) -> Optional[Type[PlacementStrategy]]:
        if name == "default":
            from spe.runtime.compiler.placement.strategies.defaultPS import DefaultPS

            return DefaultPS
        return None

    @staticmethod
    def applyTargetResults(option: OpTargetOption):
        option.catalog.opData.compileConfig.setTarget(option.target)
        option.catalog.opData.estimatedTargetStats = option.stats.exportResultStats()

    # ----------------------------------------------- Op Target Stats --------------------------------------------------

    def _determineTargetTps(self):
        # Determines target out throughput of all operators in the pipeline.
        # Each operator first collects the target out throughput's of its inputs.

        for op in self.pipeline.iterateTopological():
            cpData = self.compileDB.opCompileData[op.id]

            self._determineTargetTp(cpData)

    def _determineTargetTp(self, opData: OpCompileData):
        # Determines the target out throughput of this operator - if not specified manually
        # For sources: Calculated based on processing rate
        # For ops: Based on the min[inTps] depending on the operator maxOutputConversion

        if not opData.compileConfig.targetStats.autoTp and opData.compileConfig.targetStats.targetTp is not None:
            return

        if not opData.operator.isSource():
            inOps = opData.operator.getNeighbours(True, False)

            inTps = []
            maxTargetTps = []

            for inOp in inOps:
                iOData = self.compileDB.opCompileData[inOp.id]

                inTps.append(iOData.compileConfig.targetStats.targetTp)
                maxTargetTps.append(iOData.compileConfig.targetStats.maxTargetTp)

            if len(inTps) > 0:
                opData.compileConfig.targetStats.targetTp = opData.operator.deriveOutThroughput(min(inTps))
                opData.compileConfig.targetStats.maxTargetTp = opData.operator.deriveOutThroughput(max(maxTargetTps))
        else:
            cmp: ExecutionStatsKP = opData.getKnowledgeProvider(OpKnowledgeType.EXECUTION_STATS)
            stats = cmp.getStats()

            opData.compileConfig.targetStats.targetTp = stats.outTpStats.average if stats is not None else 0

            if opData.compileConfig.targetStats.targetTp == 0:
                opData.compileConfig.targetStats.targetTp = 30  # Random default fallback value

            opData.compileConfig.targetStats.maxTargetTp = opData.compileConfig.targetStats.targetTp
