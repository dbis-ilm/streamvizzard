from __future__ import annotations

import math
import random
from typing import Dict, TYPE_CHECKING, List, Optional, Iterator, Set, Tuple

from spe.runtime.compiler.compilerRes import CompilerRes
from spe.runtime.compiler.definitions.compileDefinitions import CompileParallelism, CompileComputeMode, CompileFramework
from spe.runtime.compiler.definitions.compileFrameworkSpecs import getSupportedFrameworks
from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from spe.runtime.compiler.placement.opTargetCatalog import OpTargetOption, OpTargetCatalog
from spe.runtime.compiler.placement.placementUtils import estimateCommunicationTime, findTargetChains
from spe.runtime.compiler.placement.strategies.placementStrategy import PlacementStrategy
from spe.common.timer import Timer
from utils.utils import valueOr, clamp, tryParseInt, tryParseFloat, remap

if TYPE_CHECKING:
    from spe.runtime.compiler.compileDB import CompileDB
    from spe.pipeline.pipeline import Pipeline
    from spe.runtime.compiler.placement.frameworkAdvisor.frameworkAdvisor import FrameworkAdvisor


class DefaultPS(PlacementStrategy):
    def __init__(self, pipeline: Pipeline, compileDB: CompileDB, config: Dict):
        super().__init__(pipeline, compileDB, config)

        # Brute Force params
        self.maxBfTime = tryParseFloat(config.get("maxBfTime"), 100)  # [s]

        # Simulated Annealing params
        self.maxIterations = tryParseInt(config.get("maxIterations"), 10000)
        self.coolingRate = remap(tryParseFloat(config.get("coolingRate"), 0.95), 0, 1, 0.99, 0.9999)

        # Score
        self.weightTransfer = clamp(tryParseFloat(config.get("scoreTransfer"), 0.25), 0, 1)
        self.weightTp = clamp(tryParseFloat(config.get("scoreTp"), 0.5), 0, 1)
        self.weightNodes = clamp(tryParseFloat(config.get("scoreNodeCount"), 0.25), 0, 1)

        self.opTargetCatalog: Dict[int, OpTargetCatalog] = {}

        self._maxFrameworkPara: Dict[CompileFramework, int] = dict()
        self._fwManualParas: Dict[CompileFramework, Set[int]] = dict()

        # Optimizations for speedup
        self._topologicalOpCatalogs: List[OpTargetCatalog] = list()
        self._pipelineSinks: List[OpTargetCatalog] = list()
        self._frameworkAdvisor: Dict[CompileFramework, Optional[FrameworkAdvisor]] = {f.framework: f.getPlacementAdvisorInstance() for f in getSupportedFrameworks()}
        self._parallelizedOptions: Dict[OpTargetOption, List[OpTargetOption]] = dict()

    def apply(self) -> CompilerRes:
        self.calculateOpTargetCatalog()
        self._topologicalOpCatalogs = [self.opTargetCatalog[op.id] for op in list(self.pipeline.iterateTopological())]
        self._pipelineSinks = [self.opTargetCatalog[op.id] for op in self.pipeline.getSinks()]

        for opCatalog in self.opTargetCatalog.values():
            for option in opCatalog.options:
                self._parallelizedOptions[option] = list(self._deviateParallelizedOptions(option, True))

        for fa in self._frameworkAdvisor.values():
            if fa is not None:
                fa.reset(self._topologicalOpCatalogs)

        alg = self.config["algorithm"]

        if alg == "BruteForce":
            return self._runBruteForce()
        elif alg == "SimulatedAnnealing":
            return self._runSimulatedAnnealing()
        elif alg == "Greedy":
            return self._runGreedy()
        elif alg == "Backtracking":
            return self._runBacktracking()

        return CompilerRes.error("No strategy to suggest targets!")

    # -------------------------------------------------- Bruteforce ----------------------------------------------------

    def _runBruteForce(self) -> CompilerRes:
        """ BruteForce is guaranteed to find the best configuration by trying out all possible combinations.
        Will be expensive on large operator graphs with high parallelism! """

        start = Timer.currentRealTime()
        its = 0

        allOperatorOptions: List[List[OpTargetOption]] = []

        # Initialize target catalog for each operator and collect all possible options

        for catalog in self._topologicalOpCatalogs:
            allOperatorOptions.append(catalog.options)

        # Run bruteForce for all combinations!

        bestScore = self.calculateOverallPerformanceScore()
        bestConstellation = self.snapshotCurrentConstellation(True)

        endIdx = len(allOperatorOptions) - 1

        def calcScore():
            nonlocal bestScore, bestConstellation, its

            its += 1
            newScore = self.calculateOverallPerformanceScore()

            if newScore.isBetterThan(bestScore, self.weightTransfer, self.weightTp, self.weightNodes):
                bestScore = newScore
                bestConstellation = self.snapshotCurrentConstellation(True)

        def handleOption(startIdx: int, option: OpTargetOption):
            # If we are at the lowest level, calculate score
            if startIdx == endIdx:
                calcScore()

            # Otherwise, iterate further down
            else:
                # Need to inherit targets first before we can cache parent ex stats
                if option.catalog.opData.metaData.inheritTarget:
                    self._handleTargetInheritance(option.catalog)

                # Our IN neighbours can now be cached since they won't be influenced by next children
                for inNCatalog in option.catalog.inNeighbours:
                    if not inNCatalog.selectedOption.calculated:
                        self.estimateFinalExecutionStats(inNCatalog)
                        inNCatalog.selectedOption.calculated = True

                iterateDown(startIdx + 1)

                # Reset for next iteration
                for inNCatalog in option.catalog.inNeighbours:
                    inNCatalog.selectedOption.calculated = False

        # Recursively iterates all nodes in topological order to cache already processed nodes for speedup

        def iterateDown(startIdx: int):
            if Timer.currentRealTime() - start > self.maxBfTime:
                return

            options = allOperatorOptions[startIdx]

            for option in options:
                for opVar in self._parallelizedOptions[option]:
                    option.catalog.selectedOption = opVar

                    handleOption(startIdx, opVar)

        iterateDown(0)

        # Collect the best overall result

        end = Timer.currentRealTime()

        for entry in bestConstellation.values():
            self.applyTargetResults(entry)

        return CompilerRes.ok(f"Completed {its} iterations in {round(end - start, 2)} s!")

    # --------------------------------------------- Simulated Annealing ------------------------------------------------

    def _runSimulatedAnnealing(self):
        """ Simulated Annealing starts with a high-temperature value, allowing the algorithm to explore the solution space
        by accepting both better and worse solutions with a certain probability [to avoid getting stuck in local optima].
        As the temperature gradually decreases, the algorithm becomes more selective, reducing randomness and converging
        toward an optimal or near-optimal solution. """

        start = Timer.currentRealTime()
        totalIterations = 0

        # Initialize with random choice for each operator

        for catalog in self.opTargetCatalog.values():
            catalog.selectedOption = catalog.getRandomOption()

        allOps = list(self.opTargetCatalog.values())

        # Initialize algorithm

        currentScore = self.calculateOverallPerformanceScore()

        bestScore = currentScore
        bestConstellation = self.snapshotCurrentConstellation()

        maxIterations = self.maxIterations
        startingTemperature = self.maxIterations
        # How likely a worse solution might be accepted to avoid getting stuck in local optima.
        temperature = startingTemperature
        # How fast the algorithm converges towards a solution. A fast cooling rate might miss out the global optimum.
        coolingRate = self.coolingRate
        minTemperature = 1e-3

        def handleOption(option: OpTargetOption):
            nonlocal currentScore, bestScore, bestConstellation

            prevOption = option.catalog.selectedOption
            option.catalog.selectedOption = option

            # Compute the new total score

            newScore = self.calculateOverallPerformanceScore()

            # Accept either if it's a better solution or accept a worse solution with some chance.
            # Key idea: avoid getting stuck in local optima.
            # The higher the temperature, the higher the probability that a worse solution is accepted.

            if newScore.isBetterThan(currentScore, self.weightTransfer, self.weightTp, self.weightNodes) or random.uniform(0, 1) < (temperature / startingTemperature):
                currentScore = newScore

                if currentScore.isBetterThan(bestScore, self.weightTransfer, self.weightTp, self.weightNodes):
                    bestScore = currentScore

                    bestConstellation = self.snapshotCurrentConstellation(True)
            else:
                option.catalog.selectedOption = prevOption

        # Run algorithm, letting it cool down with every new configuration

        for it in range(maxIterations):
            if temperature < minTemperature:
                break  # Cooled down

            totalIterations += 1

            # Pick a random operator and a new random target

            opCatalog: OpTargetCatalog = random.choice(allOps)

            newOption = opCatalog.getRandomOption()

            for opVar in self._parallelizedOptions[newOption]:
                handleOption(opVar)

            # Reduce temperature

            temperature *= coolingRate

        # Result is the found best constellation

        end = Timer.currentRealTime()

        for entry in bestConstellation.values():
            self.applyTargetResults(entry)

        return CompilerRes.ok(f"Completed {totalIterations} iterations in {round(end - start, 2)} s!")

    # ---------------------------------------------------- Greedy ------------------------------------------------------

    def _runGreedy(self):
        """ Selects the best local option for each operator in a topological order. This finds the best semi-local
        option, considering its own and input op stats (which are already calculated). """

        start = Timer.currentRealTime()
        totalIterations = 0

        # Initialize catalog with random options

        for catalog in self.opTargetCatalog.values():
            catalog.selectedOption = catalog.getRandomOption()

        for opCatalog in self._topologicalOpCatalogs:
            # Choose the best target that considers the own local options and all available neighbours

            bestPerf = None
            bestOption = None

            for option in opCatalog.options:
                for opVar in self._parallelizedOptions[option]:
                    opCatalog.selectedOption = opVar

                    score = self.calculateOverallPerformanceScore()

                    totalIterations += 1

                    if bestPerf is None or score.isBetterThan(bestPerf, self.weightTransfer, self.weightTp, self.weightNodes):
                        bestPerf = score
                        bestOption = opVar

            opCatalog.selectedOption = bestOption

        # Apply the selected results

        end = Timer.currentRealTime()

        for opCatalog in self.opTargetCatalog.values():
            self.applyTargetResults(opCatalog.selectedOption)

        return CompilerRes.ok(f"Completed {totalIterations} iterations in {round(end - start, 2)} s!")

    # ------------------------------------------------ Back Tracking ---------------------------------------------------

    def _runBacktracking(self):
        """ Iterates the pipeline in a topological order and chooses optimal local targets for each operator [Greedy].
        After each operator we iterate upwards to the beginning of the pipeline [Backtrack] step-by-step and try to
        improve the preceding parent operators based on our new local (child) option."""

        start = Timer.currentRealTime()
        totalIterations = 0

        # Initialize catalog with random options

        for catalog in self.opTargetCatalog.values():
            catalog.selectedOption = catalog.getRandomOption()

        def selectLocalOptimum(cat: OpTargetCatalog, backtrack: bool):
            # Local stage -> Find best performing local option

            bestPerf = None
            bestOption = None

            for option in cat.options:
                for opVar in self._parallelizedOptions[option]:
                    cat.selectedOption = opVar

                    score = self.calculateOverallPerformanceScore()

                    nonlocal totalIterations
                    totalIterations += 1

                    if bestPerf is None or score.isBetterThan(bestPerf, self.weightTransfer, self.weightTp, self.weightNodes):
                        bestPerf = score
                        bestOption = opVar

            cat.selectedOption = bestOption

        for i in range(len(self._topologicalOpCatalogs)):
            catalog = self._topologicalOpCatalogs[i]

            selectLocalOptimum(catalog, False)

            # Iterate upwards and try to improve

            for backtrackIdx in range(i - 1, -1, -1):
                parentCatalog = self._topologicalOpCatalogs[backtrackIdx]

                selectLocalOptimum(parentCatalog, True)

        # Terminated, current constellation -> best options | Apply results

        self.calculateOverallPerformanceScore()  # Update all stats

        end = Timer.currentRealTime()

        for opCatalog in self.opTargetCatalog.values():
            self.applyTargetResults(opCatalog.selectedOption)

        return CompilerRes.ok(f"Completed {totalIterations} iterations in {round(end - start, 2)} s!")

    # --------------------------------------------- Op Target Estimation -----------------------------------------------

    def _deviateParallelizedOptions(self, option: OpTargetOption, returnCloned: bool = False) -> Iterator[OpTargetOption]:
        """ Iterates all suitable parallelized options for the input option.
        If the option does not support parallelism, only the original option is returned.
        Otherwise, various combinations of parallelism counts will be returned based on parent and framework."""

        # Future Work: Could improve this to exclude some parallelization options that do not improve performance

        if option.supportsParallelism:
            maxFrameworkPara = self._maxFrameworkPara[option.target.framework]

            if advisor := self._frameworkAdvisor[option.target.framework]:
                maxFrameworkPara = advisor.adviceMaxParallelism(option.catalog, maxFrameworkPara)

            for para in range(maxFrameworkPara):
                resultOp = option.clone(True) if returnCloned else option

                resultOp.target.setParallelism(para + 1)

                yield resultOp
        else:
            yield option

    @staticmethod
    def _handleTargetInheritance(opCatalog: OpTargetCatalog):
        # Copy target from parent if inheritance is defined

        if opCatalog.opData.metaData.inheritTarget:
            ourOption = opCatalog.selectedOption

            if len(ourOption.catalog.inNeighbours) > 0:  # Take first neighbour if multiple
                ourOption.target.resetTarget()

                parentTarget = ourOption.catalog.inNeighbours[0].selectedOption.target

                # Only apply if parent cfg is supported by own specs
                if opCatalog.opData.specsCatalog.verifyOpCompileConfig(parentTarget):
                    ourOption.target.setTarget(parentTarget)
            else:  # No neighbour -> Rely on default vals
                ...

    def calculateOpTargetCatalog(self):
        # Setup catalog and collect distinct target options + global max parallelism for each framework

        totalChainedExTime = 0  # Worst-case, taking the slowest value

        for op in self.pipeline.iterateTopological():
            opData = self.compileDB.opCompileData[op.id]

            # Calculates a target catalog for each operator that contains all possible target options with ex stats.

            inNeighbours = [self.opTargetCatalog[n.id] for n in opData.operator.getNeighbours(True, False)]

            catalog = OpTargetCatalog(opData, inNeighbours)
            self.opTargetCatalog[opData.operator.id] = catalog

            # If this operator has a user config or should inherit its config we only consider this one
            if opData.compileConfig.manual or opData.metaData.inheritTarget:
                option = OpTargetOption(self, opData.compileConfig, catalog)
                option.supportsParallelism = False  # Fixed values

                if opData.compileConfig.manual:
                    s = self._fwManualParas.get(opData.compileConfig.framework, set())
                    s.add(opData.compileConfig.parallelismCount)
                    self._fwManualParas[opData.compileConfig.framework] = s

                # If op has no inputs but must inherit its target, choose default target values
                if opData.metaData.inheritTarget and len(opData.operator.getNeighbours(True, False)) == 0:
                    option.target.setTarget(opData.specsCatalog.createDefaultCompileConfig())

                catalog.registerOption(option)

                totalChainedExTime += valueOr(option.stats.targetExTime, 0) / option.target.parallelismCount
            else:
                worstExTime = None

                # Collect all supported combinations of compile targets
                for framework in opData.specsCatalog.frameworks:
                    for language in framework.supportedLanguages:
                        for cm in language.supportedComputeModes:
                            inCfg = OpCompileConfig()
                            inCfg.framework = framework.framework
                            inCfg.language = language.language
                            inCfg.computeMode = cm

                            option = OpTargetOption(self, inCfg, catalog)

                            # Calculate max individual parallelism for the operator

                            maxParallelism, singleNodeExTime = self.estimateIndividualMaxParallelism(option, totalChainedExTime)

                            if worstExTime is None or singleNodeExTime > worstExTime:
                                worstExTime = singleNodeExTime

                            option.supportsParallelism = maxParallelism is not None
                            inCfg.setParallelism(maxParallelism if option.supportsParallelism else 1)

                            self._maxFrameworkPara[framework.framework] = max(inCfg.parallelismCount, self._maxFrameworkPara.get(framework.framework, 1))

                            option.catalog.registerOption(option)

                totalChainedExTime += valueOr(worstExTime, 0)

    def estimateIndividualMaxParallelism(self, option: OpTargetOption, chainedTotalExTime: float) -> Tuple[Optional[int], float]:
        """ Calculates the max required level of parallelism to match the required inputTp.
         Considers worst-case chaining of all involved operators for max computational demands."""

        cfg = option.target
        lang = option.catalog.opData.specsCatalog.getFramework(cfg.framework).getLanguage(cfg.language)

        # Calc max possible overhead to neighbours (worst case scenario)

        outNeighbours = len(option.catalog.opData.operator.getNeighbours(False, True))
        overhead = self.estimateTransferOverheadToNeighbour(option, None) * outNeighbours

        # Add penalty for transferring data between compute modes

        if option.target.computeMode == CompileComputeMode.GPU:
            targetOutTp = option.stats.targetOutTp
            inDataSize = option.stats.inDataSize
            outDataSize = option.stats.totalOutDataSize
            inSerializationCost = option.stats.totalInDataSerialization + option.stats.totalInDataDeserialization
            outSerializationCost = option.stats.totalOutDataSerialization + option.stats.totalOutDataDeserialization

            overhead += estimateCommunicationTime(inDataSize, targetOutTp, self.avgGPUTransferSpeed, self.avgGPULatency) + inSerializationCost
            overhead += estimateCommunicationTime(outDataSize, targetOutTp, self.avgGPUTransferSpeed, self.avgGPULatency) + outSerializationCost

        exTime = valueOr(option.stats.targetExTime, 0) + overhead

        if not lang.supportsParallelism(cfg.computeMode, CompileParallelism.DISTRIBUTED):
            return None, exTime

        # We use targetOutTp as the max achievable output rate which we want to reach

        # How many nodes are required (at max) to match the max throughput of the data stream

        nodes = max(1, math.ceil((exTime + chainedTotalExTime) * option.stats.targetOutTp))

        if self.maxNodesCount is not None:
            nodes = clamp(nodes, 1, self.maxNodesCount)

        return nodes, exTime

    def estimateTransferOverheadToNeighbour(self, option1: OpTargetOption, option2: Optional[OpTargetOption]):
        # Calculate communication overheads to neighbour based on the different compile targets.
        # If other option is None, consider worst case

        outDataSize = option1.stats.totalOutDataSize
        targetOutTp = option1.stats.targetOutTp

        # For simplicity, we add the deserialization cost also to this operator [since our neighbour did not know about our option before]
        # In real scenarios the ser/deser might occur in a batch which is faster compared to individual elements
        serializationCost = option1.stats.totalOutDataSerialization + option1.stats.totalOutDataDeserialization

        cfg1 = option1.target

        neighbourPenalty = 0

        # Compare target with neighbour and apply penalties for distinct target params

        if option2 is None or cfg1.framework != option2.target.framework:
            # Add penalty for exchanging data between the frameworks [cluster connections]
            neighbourPenalty += estimateCommunicationTime(outDataSize, targetOutTp, self.avgConnectorTransferSpeed, self.avgConnectorTransferLatency)
            neighbourPenalty += serializationCost
            neighbourPenalty += self.targetSwitchPenalty

        # Only consider parallelism if its defined yet

        if option2 is None or cfg1.parallelismCount != option2.target.parallelismCount:
            # Add penalty for transferring data between processing nodes [single round of data distribution]
            # We assume a full data shuffle to ensure even load distribution

            neighbourPenalty += estimateCommunicationTime(outDataSize, targetOutTp, self.avgNodeTransferSpeed, self.avgNodeTransferLatency)
            neighbourPenalty += serializationCost
            neighbourPenalty += self.targetSwitchPenalty

        if advisor := self._frameworkAdvisor[option1.target.framework]:
            neighbourPenalty = advisor.adviceTransferCostToOutNeighbour(option1, option2, neighbourPenalty)

        return neighbourPenalty  # Res in seconds

    def estimateFinalExecutionStats(self, opCatalog: OpTargetCatalog):
        # Calculate the estimated exTimes for the selected option of each operator.
        # Considers the overhead for communicating with outNeighbours [their selected option].

        self._handleTargetInheritance(opCatalog)

        ourOption = opCatalog.selectedOption

        # Add overhead to all (out) neighbours we need to communicate to

        overhead = 0

        for nCatalog in opCatalog.outNeighbours:
            overhead += self.estimateTransferOverheadToNeighbour(ourOption, nCatalog.selectedOption)

        # Add penalty for transferring data between compute modes

        if ourOption.target.computeMode == CompileComputeMode.GPU:
            inDataSize = ourOption.stats.inDataSize
            outDataSize = ourOption.stats.totalOutDataSize
            targetOutTp = ourOption.stats.targetOutTp

            inSerializationCost = ourOption.stats.totalInDataSerialization + ourOption.stats.totalInDataDeserialization
            outSerializationCost = ourOption.stats.totalOutDataSerialization + ourOption.stats.totalOutDataDeserialization

            overhead += estimateCommunicationTime(inDataSize, targetOutTp, self.avgGPUTransferSpeed, self.avgGPULatency) + inSerializationCost
            overhead += estimateCommunicationTime(outDataSize, targetOutTp, self.avgGPUTransferSpeed, self.avgGPULatency) + outSerializationCost

        # Our estimated ex time is slowed down by the collected overhead

        exTime = valueOr(ourOption.stats.targetExTime, 0)  # Single-Node

        if opCatalog.opData.operator.isSource():
            # For sources, we assume that the incoming data (from arbitrary sources) must be deserialized
            # Additional source execution durations/overhead can only be estimated by utilizing cost models

            exTime += ourOption.stats.totalOutDataDeserialization

        ourOption.stats.estTransferTime = overhead
        ourOption.stats.estCalcTime = exTime

    def estimateFinalThroughputs(self):
        # Find operator chains with same framework/language/computeMode

        chains = findTargetChains(self._topologicalOpCatalogs)

        # Calculate total execution load per chain (per executor) according to target tp

        for chain in chains:
            if advisor := self._frameworkAdvisor[chain.framework]:
                advisor.adviceExecutionThroughput(chain.targets)

        # Iterate topological and determine final, reachable tp values (considering actual inTp of neighbours)

        for opCatalog in self._topologicalOpCatalogs:
            ourOption = opCatalog.selectedOption

            if ourOption is None:
                continue

            maxCalcOutTp = ourOption.stats.estOutTp  # Potentially calculated by advisor

            if maxCalcOutTp is None:  # Default fallback
                maxCalcOutTp = (1 / ourOption.stats.estTotalExTime) * ourOption.target.parallelismCount

            # Limit outTp to the estimated inTp [min of estimated outTps of inputs - need to be calculated before]

            minInputOutTps: Optional[float] = None  # Sources do not have neighbours

            for nCatalog in opCatalog.inNeighbours:
                parentOut = nCatalog.selectedOption.stats.estOutTp
                minInputOutTps = min(minInputOutTps, parentOut) if minInputOutTps is not None else parentOut

            # Derive max achievable outTp by inTp | Can't produce more data than we receive
            # For sources, overhead might slow down the source output rate, if too high
            # Here we assume, the targetTp is the actual data rate that can be produced by the source

            maxDerivedOutTp = opCatalog.opData.operator.deriveOutThroughput(minInputOutTps) if minInputOutTps is not None \
                else ourOption.stats.targetOutTp

            ourOption.stats.estOutTp = min(maxCalcOutTp, maxDerivedOutTp)

    def calculateOverallPerformanceScore(self, startCat: Optional[OpTargetCatalog] = None) -> PerformanceScore:
        # Calculate a score for the overall throughput and execution time of all operators.
        # Tp: Difference between estimated and target throughput for the data sinks, weighted with influence of tp (target=maximize)
        # Transfer: Sum of all estimated operator data transfer costs (to OUT neighbours) (target=minimize)
        # Nodes: Sum of all utilized nodes per framework (target=minimize)

        tpScore = 0
        nodeScore = 0
        transferScore = 0

        skipCats = startCat is not None

        fwMaxNodes: Dict[CompileFramework, int] = dict()

        for opCatalog in self._topologicalOpCatalogs:
            if skipCats and opCatalog == startCat:
                skipCats = False

            if skipCats or opCatalog.selectedOption is None:
                continue

            if not opCatalog.selectedOption.calculated:
                self.estimateFinalExecutionStats(opCatalog)

            stats = opCatalog.selectedOption.stats

            transferScore += stats.estTransferTime

            # Register max level of parallelism per framework
            current = fwMaxNodes.get(opCatalog.selectedOption.target.framework, 0)
            fwMaxNodes[opCatalog.selectedOption.target.framework] = max(current, opCatalog.selectedOption.target.parallelismCount)

        self.estimateFinalThroughputs()

        totalTargetTp = 0  # Used to normalize resulting tp value

        for sinkCatalog in self._pipelineSinks:
            if sinkCatalog.selectedOption is None:
                continue

            stats = sinkCatalog.selectedOption.stats

            if stats.targetOutTp > 0:
                # Calculate how close the reached tp is compared to the target tp, no benefit for higher tp

                score = min(1, stats.estOutTp / stats.targetOutTp)
                tpScore += score * stats.targetOutTp  # Weight with targetTp -> Higher impact for higher target tps
                totalTargetTp += stats.targetOutTp

        for n in fwMaxNodes.values():
            nodeScore += n

        return DefaultPS.PerformanceScore(transferScore, tpScore / totalTargetTp if totalTargetTp != 0 else 0, nodeScore)

    def snapshotCurrentConstellation(self, cloneTarget: bool = False):
        return {v.opData: v.selectedOption.clone(cloneTarget) for v in self.opTargetCatalog.values()}

    class PerformanceScore:
        def __init__(self, transferScore: float, tpScore: float, nodeScore: float):
            self.tpScore = tpScore
            self.nodeScore = nodeScore
            self.transferScore = transferScore

        def isBetterThan(self, other: DefaultPS.PerformanceScore, wTf: float, wTp: float, wNode: float):
            return self.getCombinedScore(other, wTf, wTp, wNode) > 0.5

        def getCombinedScore(self, other: DefaultPS.PerformanceScore, wTf: float, wTp: float, wNode: float):
            # CombinedScore < 0.5 -> worse
            # CombinedScore == 0.5 -> equal
            # CombinedScore > 0.5 -> better

            tpRatio, nodeRatio, transferRatio = self._calcScores(other)

            return (transferRatio * wTf + tpRatio * wTp + nodeRatio * wNode) / (wTf + wTp + wNode)

        @staticmethod
        def _calcScore(val1: float, val2: float):
            # Scores difference in stats in range [-1,1] (1 -> a much bigger than b)
            # 0 -> Equal
            # < 0 -> Worse
            # > 0 -> Better

            dSum = abs(val1) + abs(val2)

            rawScore = ((val1 - val2) / dSum) if dSum != 0 else 0

            # Remap to [0,1]
            # 0.5 -> Equal
            # < 0.5 -> Worse
            # > 0.5 -> Better

            return (rawScore + 1) / 2

        def _calcScores(self, other: DefaultPS.PerformanceScore):
            tpRatio = self._calcScore(self.tpScore, other.tpScore)
            nodeScore = self._calcScore(other.nodeScore, self.nodeScore)  # inv for min
            transferScore = self._calcScore(other.transferScore, self.transferScore)  # inv for min

            return tpRatio, nodeScore, transferScore
