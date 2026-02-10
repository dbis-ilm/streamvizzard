from __future__ import annotations
from typing import Dict, List, Iterable, Set, Optional, TYPE_CHECKING

from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework
from spe.runtime.compiler.placement.opTargetCatalog import OpTargetOption, OpTargetCatalog

if TYPE_CHECKING:
    from spe.runtime.compiler.placement.frameworkAdvisor.frameworkAdvisor import FrameworkAdvisor

# Avg estimations for considering network latency. Future Work: Exposed values
# Future Work: Calc transfer in batches in general

AVG_BATCH_SIZE = 50_000  # bytes
AVG_FLUSH_INTERVAL = 0.1  # s [every 100ms]


class DataExchangeOverhead:
    def __init__(self, latency: float = 0, transfer: float = 0, serialization: float = 0):
        self.latency = latency
        self.transfer = transfer
        self.serialization = serialization

    def add(self, other: DataExchangeOverhead) -> DataExchangeOverhead:
        self.latency += other.latency
        self.transfer += other.transfer
        self.serialization += other.serialization

        return self

    def multiply(self, val: float) -> DataExchangeOverhead:
        self.latency *= val
        self.transfer *= val
        self.serialization *= val

        return self

    def getTotal(self) -> float:
        return self.latency + self.transfer + self.serialization


def estimateCommunicationTime(dataSizePerElm: float, elmRate: float, serializationTime: float,
                              avgNetworkSpeed: float, avgNetworkLatency: float,
                              batchSize: int = AVG_BATCH_SIZE, flushInterval: float = AVG_FLUSH_INTERVAL) -> DataExchangeOverhead:
    # ElmSize: bytes, elmRate: elm/s, serializationTime: s, BatchSize: bytes, FlushInterval: seconds

    transferTime = dataSizePerElm / avgNetworkSpeed

    if elmRate == 0 or dataSizePerElm == 0:
        latency = 0
    else:
        tuplesPerBatch = min(batchSize / dataSizePerElm, elmRate * flushInterval)

        latency = avgNetworkLatency / tuplesPerBatch

    return DataExchangeOverhead(latency, transferTime, serializationTime)


class TargetChain:
    def __init__(self, framework: CompileFramework):
        self.framework = framework
        self.targets: List[OpTargetOption] = list()

    def merge(self, other: TargetChain):
        self.targets.extend(other.targets)


def findTargetChains(topologicalCats: Iterable[OpTargetCatalog],
                     advisor: Dict[CompileFramework, Optional[FrameworkAdvisor]]) -> List[TargetChain]:
    """ Finds chains of adjacent targets with same framework/language/computeMode """

    chainLookup: Dict[OpTargetOption, TargetChain] = dict()
    uniqueChains: Set[TargetChain] = set()

    for opCatalog in topologicalCats:
        option = opCatalog.selectedOption

        if option is None:
            continue

        chain = None

        for neighbour in option.catalog.inNeighbours:
            neighbourOption = neighbour.selectedOption

            if ((neighbourOption.target.framework == option.target.framework) and
                    (neighbourOption.target.language == option.target.language) and
                    (neighbourOption.target.computeMode == option.target.computeMode) and
                    (advisor[option.target.framework].adviceCanChain(option, neighbourOption))):

                # Same chain

                prevChain = chainLookup[neighbourOption]

                if chain is None:
                    chain = prevChain

                # Merge prev chain into this [for multiple chainable IN neighbours]
                # Do not merge if we already have the same chain in our neighbours

                elif chain != prevChain:
                    for op in prevChain.targets:
                        chainLookup[op] = chain

                    uniqueChains.remove(prevChain)
                    chain.merge(prevChain)

        if chain is None:  # First op in chain
            chain = TargetChain(option.target.framework)
            uniqueChains.add(chain)

        chain.targets.append(option)
        chainLookup[option] = chain

    return list(uniqueChains)
