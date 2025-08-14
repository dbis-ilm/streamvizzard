from __future__ import annotations

import copy
import random
from typing import TYPE_CHECKING, Optional, List, Dict

from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from spe.runtime.compiler.placement.knowledgeProvider.costModelKP import CostModelKP
from spe.runtime.compiler.placement.knowledgeProvider.executionStatsKP import ExecutionStatsKP
from spe.runtime.compiler.placement.knowledgeProvider.opKnowledgeProvider import OpKnowledgeType
from utils.utils import valueOr

if TYPE_CHECKING:
    from spe.runtime.compiler.opCompileData import OpCompileData
    from spe.runtime.compiler.placement.strategies.placementStrategy import PlacementStrategy


class OpTargetCatalog:
    def __init__(self, opData: OpCompileData, inNeighbours: List[OpTargetCatalog]):
        self.opData = opData

        self.options: List[OpTargetOption] = list()
        self.selectedOption: Optional[OpTargetOption] = None

        self.inNeighbours = inNeighbours
        self.outNeighbours: List[OpTargetCatalog] = list()

        for inN in inNeighbours:
            inN.outNeighbours.append(self)

    def registerOption(self, option: OpTargetOption):
        self.options.append(option)

        if self.selectedOption is None:
            self.selectedOption = option

    def getRandomOption(self) -> OpTargetOption:
        return random.choice(self.options)


class OpTargetOption:
    def __init__(self, strategy: PlacementStrategy, target: OpCompileConfig,
                 catalog: OpTargetCatalog):
        self.catalog = catalog
        self.target = target
        self.stats = OpTargetOptionStats.load(strategy, self)

        self.supportsParallelism = False
        self.calculated = False  # For optimization

    def clone(self, cloneTarget: bool = False):
        shallowCopy = copy.copy(self)

        # Clone target if forced or if it is inherited by parent, to avoid future modifications

        if cloneTarget or self.catalog.opData.metaData.inheritTarget:
            shallowCopy.target = copy.deepcopy(self.target)

        # Now clone the stats deep to avoid subsequent modification

        shallowCopy.stats = copy.deepcopy(shallowCopy.stats)

        return shallowCopy


class OpTargetOptionStats:
    def __init__(self):
        # General stats

        # We assume, that operators push their total OUT data to neighbours, independent on what "socket" is actually used
        self.totalOutDataSize = 0  # [bytes]
        self.inDataSize = 0  # [bytes] | Only actual data the operator processes
        self.totalOutDataSerialization = 0.0  # [s]
        self.totalOutDataDeserialization = 0.0  # [s]
        self.totalInDataSerialization = 0.0  # [s]
        self.totalInDataDeserialization = 0.0  # [s]

        # Target values [derived by execution stats or user-defined]

        self.targetExTime = 1 / 1_000_000  # [s] default val 1us
        # User-defined or calculated actual max achievable outTP - based on slowest IN neighbour
        self.targetOutTp: Optional[float] = None  # [tup/s]
        # Calculated theoretical max achievable outTP - based on fastest IN neighbour
        self.highestOutTp: Optional[float] = None  # [tup/s]

        # Estimated values [dependent on the neighbours]

        self.estCalcTime: Optional[float] = None  # Single-Node calculation time per tuple
        self.estTransferTime: Optional[float] = None  # Communication overhead time per tuple
        self.estOutTp: Optional[float] = None

    @property
    def estTotalExTime(self):
        """ Total single-node execution time per tuple, including communication overhead. """

        return self.estCalcTime + self.estTransferTime

    def exportResultStats(self) -> OpTargetStatsEstimation:
        return OpTargetStatsEstimation(self.estCalcTime, self.estTransferTime, self.estOutTp,
                                       self.totalOutDataSize)

    @staticmethod
    def load(strategy: PlacementStrategy, option: OpTargetOption):
        optionStats = OpTargetOptionStats()

        opData = option.catalog.opData
        cfg = option.target

        opData.compileConfig.targetStats.exTimeSource = "None"

        # CM, ExStats perform their own caching (respecting params such as CM Path ...),
        # which is persistent during the whole compilation session.

        # Try to get values from the execution stats. If CM values are available, those are preferred over the ex stats.
        # Execution stats will also be considered even if the compile target does not match exactly (language, framework, ...)
        # Reason: Prefer some statistics (even if not 100% fitting) over none at all

        cmp: ExecutionStatsKP = opData.getKnowledgeProvider(OpKnowledgeType.EXECUTION_STATS)
        stats = cmp.getStats()

        if stats is not None:
            optionStats.targetExTime = stats.exTimeStats.average
            opData.compileConfig.targetStats.exTimeSource = "ExecutionStats"

            optionStats.totalOutDataSize = stats.outDataSizeStats.average
            optionStats.inDataSize = stats.inDataSizeStats.average
            optionStats.totalOutDataSerialization = stats.outDataSerialization.average
            optionStats.totalOutDataDeserialization = stats.outDataDeserialization.average
            optionStats.totalInDataSerialization = stats.inDataSerialization.average
            optionStats.totalInDataDeserialization = stats.inDataDeserialization.average

        # Try to get (override) values from available cost models:

        if strategy.costModelPath is not None:
            cmp: CostModelKP = opData.getKnowledgeProvider(OpKnowledgeType.COST_MODEL)

            cmExTime = cmp.predictExecutionTime(strategy.costModelPath, cfg.framework, cfg.language, cfg.computeMode, stats)

            if cmExTime is not None:
                optionStats.targetExTime = cmExTime
                opData.compileConfig.targetStats.exTimeSource = "CostModel"

        # -- Load target throughput statistics ---

        optionStats.targetOutTp = valueOr(opData.compileConfig.targetStats.targetTp, 0)
        optionStats.highestOutTp = valueOr(opData.compileConfig.targetStats.maxTargetTp, optionStats.targetOutTp)

        # Set ex time if specified by user, otherwise take previous value from stats/cm
        if not opData.compileConfig.targetStats.autoExTime:
            optionStats.targetExTime = opData.compileConfig.targetStats.targetExTime

        opData.compileConfig.targetStats.targetExTime = valueOr(optionStats.targetExTime, 0)

        return optionStats


class OpTargetStatsEstimation:
    def __init__(self, estCalcTime: float, estTransferTime: float, estOutTp: float,
                 outDataSize: float):
        self.estCalcTime = estCalcTime  # Seconds (per Node)
        self.estTransferTime = estTransferTime  # Seconds (per Tuple)
        self.estOutTp = estOutTp  # Tuples / second
        self.outDataSize = outDataSize  # Bytes

    def toJSON(self) -> Dict:
        return {"estExTime": round((self.estTransferTime + self.estCalcTime) * 1000, 2),
                "estTransferTime": round(self.estTransferTime * 1000, 2), "estOutTp": round(self.estOutTp, 2),
                "outDataSize": round(self.outDataSize / 1000, 2)}
