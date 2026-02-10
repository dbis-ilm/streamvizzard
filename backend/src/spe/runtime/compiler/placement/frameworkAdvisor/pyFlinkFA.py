from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from spe.pipeline.operators.base.operators.windows.windowOperator import WindowOperator
from spe.runtime.compiler.placement.frameworkAdvisor.frameworkAdvisor import FrameworkAdvisor
from spe.runtime.compiler.placement.placementUtils import estimateCommunicationTime, DataExchangeOverhead

if TYPE_CHECKING:
    from spe.runtime.compiler.placement.opTargetCatalog import OpTargetOption, OpTargetOptionStats
    from spe.runtime.compiler.placement.strategies.placementStrategy import PlacementStrategy


class PyFlinkFA(FrameworkAdvisor):
    # Future Work: Expose values
    IPC_LATENCY = 0.000_01  # 10us in s
    IPC_BANDWIDTH = 150 * 1_000_000  # 150MB/s in bytes/s

    def adviceTransferCostToOutNeighbour(self, ps: PlacementStrategy, option: OpTargetOption,
                                         neighbour: Optional[OpTargetOption],
                                         current: DataExchangeOverhead) -> DataExchangeOverhead:
        if neighbour is None:
            if isinstance(option.catalog.opData.operator, WindowOperator):
                # Estimated worst-case cost for window (does not consider window data size)
                return current.add(option.stats.totalOutDataSerialization * 3 + 3 * self.IPC_LATENCY)

            return current

        if option.target.framework == neighbour.target.framework or neighbour.catalog.opData.metaData.inheritTarget:
            # Future Work: Check, if we need an inter-process-data-transfer for other ops -> currently mostly sources!

            neighbourOp = neighbour.catalog.opData.operator

            if isinstance(neighbourOp, WindowOperator):
                # Data tuples are transferred towards the JVM (per element state updates)

                # 2 transfers, Python->JVM for add value + JVM->Python for window evaluation
                IPCCostToWindow = self.estimateIPCTransferCost(option.stats, False).multiply(2)  # Cost per Tuple to window

                if option.target.parallelismCount > 1:
                    # Additional key_by serialization estimation
                    IPCCostToWindow.serialization += option.stats.totalOutDataSerialization

                    # Additional key_by shuffle cost
                    shuffleSer = option.stats.totalOutDataSerialization + option.stats.totalOutDataDeserialization
                    IPCCostToWindow.add(estimateCommunicationTime(option.stats.totalOutDataSize, option.stats.highestOutTp,
                                                                  shuffleSer, ps.avgNodeTransferSpeed, ps.avgNodeTransferLatency))

                return current.add(IPCCostToWindow)

        return current

    @staticmethod
    def estimateIPCTransferCost(stats: OpTargetOptionStats, fromJVM: bool) -> DataExchangeOverhead:
        # Flink bundles tuples to exchange with the Python process for better performance.
        # For reasonable values (bundleSize & bundleTime), the overhead is neglectable in most cases.

        bundleSize = 1000  # Elms
        bundleTime = 1.0  # s

        batchSize = max(1, int((stats.highestOutTp / float(bundleSize)) * stats.totalOutDataSize))

        # Serialized+Deserialized (JVM+Python side)
        serCost = stats.totalOutDataDeserialization + stats.totalOutDataSerialization

        return estimateCommunicationTime(stats.totalOutDataSize, stats.highestOutTp, serCost, PyFlinkFA.IPC_BANDWIDTH,
                                         PyFlinkFA.IPC_LATENCY, batchSize=batchSize, flushInterval=bundleTime)

    def adviceCanChain(self, ourOp: OpTargetOption, inNeighbourOp: OpTargetOption) -> bool:
        # In our current model, we assume that all threads on the taskManager slot share a single CPU core [worstCase]
        # and are therefore "chained" together - independent of real SubTasks distribution and JVM separation.

        # Distributed Windows require a redistribution [rebalance]
        # if isinstance(inNeighbourOp.catalog.opData.operator, WindowProcessor) and inNeighbourOp.target.parallelismCount > 1:
        #     return False
        #
        # # If we are a window, we can't chain to our inNeighbour since the stream is hashed/keyed
        # elif isinstance(ourOp.catalog.opData.operator, WindowOperator):
        #     return False

        return True
