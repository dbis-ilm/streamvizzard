from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from spe.runtime.compiler.placement.frameworkAdvisor.frameworkAdvisor import FrameworkAdvisor

if TYPE_CHECKING:
    from spe.runtime.compiler.placement.opTargetCatalog import OpTargetCatalog, OpTargetOption


class PyFlinkFA(FrameworkAdvisor):
    def adviceMaxParallelism(self, opCatalog: OpTargetCatalog, maxPara: int) -> int:
        # Due to the (current) absence of event times and proper order handling we do not recommend source parallelism > 1

        if opCatalog.opData.operator.isSource():
            return 1

        return maxPara

    def adviceTransferCostToOutNeighbour(self, option: OpTargetOption, neighbour: Optional[OpTargetOption], currentCost: float) -> float:
        if neighbour is None:
            return currentCost  # TODO: Worst case cost

        if option.target.framework == neighbour.target.framework:
            # TODO: Check, if we need an inter-process-data-transfer (consider bundle size)
            ...

        return currentCost
