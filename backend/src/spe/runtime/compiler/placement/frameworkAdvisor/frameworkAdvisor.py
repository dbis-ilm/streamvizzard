from __future__ import annotations
from abc import ABC
from typing import TYPE_CHECKING, Optional, Iterable

if TYPE_CHECKING:
    from spe.runtime.compiler.definitions.compileFrameworkSpecs import CompileFrameworkSpecs
    from spe.runtime.compiler.placement.opTargetCatalog import OpTargetCatalog, OpTargetOption


class FrameworkAdvisor(ABC):
    """ Provides additional information during the placement of the operators across the available frameworks. """

    def __init__(self, framework: CompileFrameworkSpecs):
        self.framework = framework

    def reset(self, opCatalogs: Iterable[OpTargetCatalog]):
        """ Called before a new placement calculation should start. """

    def adviceMaxParallelism(self, opCatalog: OpTargetCatalog, maxPara: int) -> int:
        """ Advices the max parallelism of the operator based on the proposed max parallelism by the placement strategy. """

        return maxPara

    def adviceExecutionThroughput(self, chainedOps: Iterable[OpTargetOption]):
        """ Advices the estimated throughput of all adjacent operators of the same chain.
        Considers the influence of the executor utilization on the resulting execution times of operators.
        Stateless, can also handle multiple disconnected operator chains of same framework. """

        # Assumption: Chained operators will share the same computation resources.
        # Simplification: We do not consider (yet) full task-slot awareness of the final pipeline and just estimate
        # how to CPU load might be distributed later on (sequential load distribution by executor order)
        # -> First executor always gets all tasks, second executor only tasks from ops with para >= 2, ...

        totalExLoad = []

        for target in chainedOps:
            targetTpPerEx = target.stats.targetOutTp / target.target.parallelismCount
            loadPerEx = target.stats.estTotalExTime * targetTpPerEx  # Each executor performs full operator function

            for para in range(target.target.parallelismCount):
                if para < len(totalExLoad):
                    totalExLoad[para] += loadPerEx
                else:
                    totalExLoad.append(loadPerEx)

        # Calculate the throughput correction factor per executor
        # This reflects, how much of its load each executor can achieve [0,1]

        correctionFactors = [(min(1, 1 / load) if load != 0 else 1) for load in totalExLoad]  # How much of the load fits into a "budget" of 1 second ex time

        # Adapt the estimated tp for each operator in chain based on correction factor
        # Results in the max achievable throughput (through calculation) based on the targetTp

        # At most, the operator may achieve the determined targetOutTp [considered during load estimation above].
        # However, this value might have been limited by a slow input neighbour.
        # Apply correction factor to highestOutTp, which reflects the fastest input data stream for this operator
        # (pre-neighbour-limiting), to account for still achieving the targetOutTp rate even after correction.

        for target in chainedOps:
            targetTpPerEx = target.stats.targetOutTp / target.target.parallelismCount
            highestTargetTpPerEx = target.stats.highestOutTp / target.target.parallelismCount

            target.stats.estOutTp = 0

            for para in range(target.target.parallelismCount):  # Sum tp of individual executors
                target.stats.estOutTp += min(targetTpPerEx, correctionFactors[para] * highestTargetTpPerEx)

    def adviceTransferCostToOutNeighbour(self, option: OpTargetOption, neighbour: Optional[OpTargetOption], currentCost: float) -> float:
        return currentCost
