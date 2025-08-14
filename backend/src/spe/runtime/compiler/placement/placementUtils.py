from __future__ import annotations
from typing import Dict, List, Iterable, Set

from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework
from spe.runtime.compiler.placement.opTargetCatalog import OpTargetOption, OpTargetCatalog

# Avg estimations for considering network latency. Future Work: Could also be exposed to the user
# Future Work: Calc transfer in batches in general

AVG_BATCH_SIZE = 50_000  # bytes
AVG_FLUSH_INTERVAL = 0.1  # s [every 100ms]


def estimateCommunicationTime(avgDataSize: float, avgDataRate: float, avgNetworkSpeed: float, avgNetworkLatency: float):
    transferTime = avgDataSize / avgNetworkSpeed

    if avgDataRate == 0 or avgDataSize == 0:
        latency = 0
    else:
        tuplesPerBatch = min(AVG_BATCH_SIZE / avgDataSize, avgDataRate * AVG_FLUSH_INTERVAL)

        latency = avgNetworkLatency / tuplesPerBatch

    return transferTime + latency


class TargetChain:
    def __init__(self, framework: CompileFramework):
        self.framework = framework
        self.targets: List[OpTargetOption] = list()

    def merge(self, other: TargetChain):
        self.targets.extend(other.targets)


def findTargetChains(topologicalCats: Iterable[OpTargetCatalog]) -> List[TargetChain]:
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
                    (neighbourOption.target.computeMode == option.target.computeMode)):

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
