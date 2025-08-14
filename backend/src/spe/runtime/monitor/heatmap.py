from enum import Enum
from typing import Dict, Optional

from spe.pipeline.operators.operator import Operator
from spe.pipeline.pipeline import Pipeline


class HeatmapType(Enum):
    NONE = 0,
    DATA_SIZE = 2,
    OP_RUNTIME = 3


class HeatmapResult:
    def __init__(self, opRating: Dict[Operator, float], minVal, maxVal, legendSteps):
        self.opRating = opRating
        self.minVal = minVal
        self.maxVal = maxVal
        self.legendSteps = legendSteps

    def hasData(self) -> bool:
        return len(self.opRating) > 0


class Heatmap:
    def __init__(self):
        self._currentType = HeatmapType.NONE

    def changeType(self, hmType: int):
        if hmType == 2:
            self._currentType = HeatmapType.DATA_SIZE
        elif hmType == 3:
            self._currentType = HeatmapType.OP_RUNTIME
        else:
            self._currentType = HeatmapType.NONE

    def isRequested(self) -> bool:
        return self._currentType is not HeatmapType.NONE

    def calculate(self, pipeline: Pipeline) -> Optional[HeatmapResult]:
        if self._currentType == HeatmapType.DATA_SIZE:
            return self._calculateDataSizeHM(pipeline)
        elif self._currentType == HeatmapType.OP_RUNTIME:
            return self._calculateOpRuntimeHM(pipeline)

        return None

    @staticmethod
    def _calculateDataSizeHM(pipeline: Pipeline) -> HeatmapResult:
        # Calc min/max values for all operators

        operatorHMRating: Dict[Operator, float] = dict()

        minDataSize = float("inf")
        maxDataSize = 0

        elements = []

        for op in pipeline.getAllOperators():
            operatorHMRating[op] = 0

            size = op.getMonitor().getAvgDataSize()

            if size > maxDataSize:
                maxDataSize = size

            if size < minDataSize:
                minDataSize = size

            elements.append((op, size))

        # Assign rating based on min/max

        return Heatmap._calculateBucketHM(minDataSize, maxDataSize, elements, operatorHMRating, 1/1000)

    @staticmethod
    def _calculateOpRuntimeHM(pipeline: Pipeline) -> HeatmapResult:
        # Calc min/max values for all operators

        operatorHMRating: Dict[Operator, float] = dict()

        minRT = float("inf")
        maxRT = 0

        elements = []

        for op in pipeline.getAllOperators():
            operatorHMRating[op] = 0

            if op.isSource():
                continue

            rt = op.getMonitor().getAvgExecutionTime()

            if rt > maxRT:
                maxRT = rt

            if rt < minRT:
                minRT = rt

            elements.append((op, rt))

        return Heatmap._calculateBucketHM(minRT, maxRT, elements, operatorHMRating)

    @staticmethod
    def _calculateBucketHM(minRT: float, maxRT: float, elements: list,
                           operatorHMRating: Dict[Operator, float],
                           valScaleFac: float = 1) -> HeatmapResult:
        if minRT == maxRT:
            # Rating is always 0 because min=max

            for e in elements:
                operatorHMRating[e[0]] = 0

            return HeatmapResult(operatorHMRating, minRT, maxRT, [])
        else:
            # Distribute values into buckets

            mhSteps = []

            elements.sort(key=lambda tup: tup[1])

            # Distribute values into buckets

            maxBuckets = 5
            totalDist = maxRT - minRT

            buckets = []

            # First every element gets his own bucket -> but only unique values

            elL = len(elements)

            i = 0
            while i < elL:
                bv = elements[i][1]

                # Search if as long as next element has same val

                for j in range(i + 1, elL):
                    bj = elements[j][1]

                    if bj == bv:
                        i += 1
                    else:
                        break

                buckets.append(i + 1)

                i += 1

            # Merge elements from different buckets until we fulfill the bucket amount constraint

            while len(buckets) > maxBuckets:
                # Find bucket to merge next element into (most small difference in value)
                bucketIDTOMerge = None
                smallestVal = 0

                for bID in range(0, len(buckets) - 1):
                    b = buckets[bID]
                    rightElOfThisBucket = elements[b - 1]
                    nextElement = elements[b]

                    d = (nextElement[1] - rightElOfThisBucket[1]) / totalDist

                    if bucketIDTOMerge is None or d <= smallestVal:
                        bucketIDTOMerge = bID
                        smallestVal = d

                # Merge bucket with next val

                b = buckets[bucketIDTOMerge] + 1
                buckets[bucketIDTOMerge] = b

                # Check if we need to remove next bucket in case its empty

                bNext = buckets[bucketIDTOMerge + 1]
                if b >= bNext:
                    del buckets[bucketIDTOMerge + 1]

            # Now distribute rankings to the buckets

            bl = len(buckets)

            bucketBorderWidth = 0.05
            minBucketRating = 0.15

            totalAvailableBucketRating = (1 - (bl - 1) * bucketBorderWidth)

            # Calculate value of each bucket considering min values

            bucketRankings = []
            totalFixedBucketRatingV = 0  # Total value of buckets that were clamped to min
            totalVariableBucketRatingV = 0  # Total value of remaining buckets that need to be adapted

            for bID in range(0, bl):
                b = buckets[bID]
                lastB = buckets[bID - 1] - 1 if bID > 0 else 0

                bucketRange = elements[b - 1][1] - elements[lastB][1]
                bucketRating = bucketRange / totalDist

                if bucketRating <= minBucketRating:
                    bucketRankings.append(minBucketRating)

                    totalFixedBucketRatingV += minBucketRating
                else:
                    bucketRankings.append(bucketRating)

                    totalVariableBucketRatingV += bucketRating

            # Normalize values to totalAvailableBucketRating considering the min values than increased rating

            for bID in range(0, bl):
                r = bucketRankings[bID]

                if r > minBucketRating:
                    r = (1 - totalFixedBucketRatingV) * (r / totalVariableBucketRatingV)  # Might be < minRating..

                bucketRankings[bID] = r * totalAvailableBucketRating

            # Finally, assign real ratings for each operator

            totalBucketRating = 0

            for bID in range(0, bl):
                b = buckets[bID]
                lastB = buckets[bID - 1] - 1 if bID > 0 else 0

                bucketRange = elements[b - 1][1] - elements[lastB][1]
                bucketRating = bucketRankings[bID]

                if bID < bl - 1:
                    mhSteps.append((elements[b - 1][1] * valScaleFac,
                                    totalBucketRating + bucketRating + bucketBorderWidth))

                currentBucketVal = elements[lastB][1]
                for i in range(lastB + 1, b):
                    element = elements[i]

                    ranking = (element[1] - currentBucketVal) / bucketRange if bucketRange > 0 else 0
                    currentBucketVal = element[1]

                    operatorHMRating[element[0]] = totalBucketRating + (bucketRating * ranking)

                totalBucketRating += bucketRating + bucketBorderWidth

            return HeatmapResult(operatorHMRating, minRT * valScaleFac, maxRT * valScaleFac, mhSteps)
