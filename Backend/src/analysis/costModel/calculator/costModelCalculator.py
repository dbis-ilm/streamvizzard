import logging
import traceback
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import BayesianRidge, ARDRegression, \
    PassiveAggressiveRegressor, ElasticNet, Ridge

from analysis.costModel.calculator.costModelCandidate import CostModelCandidate
from analysis.costModel.calculator.genericCC import GenericCC
from analysis.costModel.calculator.polynomialCC import PolynomialCC
from analysis.costModel.configurations.costModelOpSetups import CostModelFeatureStats, CostModelOpCfg
from analysis.costModel.costModel import CostModel, CostModelVariant, CostModelTarget, CostModelEnv
from analysis.costModel.operatorEntry import OperatorEntry, ExecutionRecording
from utils.utils import printWarning


class CostModelVisualization(Enum):
    NONE = 1
    BEST = 2
    COMPARISON = 3


class CostModelCalculator:
    def __init__(self):
        self._bucketSize = 50

    def calculateBestModel(self, op: OperatorEntry, visResult: CostModelVisualization, printIntermediate: bool) -> Optional[CostModel]:
        # Data storage for each target

        inputData: Dict[Tuple[CostModelEnv, CostModelTarget], Any] = dict()
        outputData: Dict[Tuple[CostModelEnv, CostModelTarget], Any] = dict()

        # Find best model candidates for each mode

        bestModels: Dict[Tuple[CostModelEnv, CostModelTarget], Optional[CostModelVariant]] = dict()
        bestCandidates: Dict[Tuple[CostModelEnv, CostModelTarget], Optional[CostModelCandidate]] = dict()

        allModels: Dict[Tuple[CostModelEnv, CostModelTarget], List[CostModelVariant]] = dict()

        for targetConfig in op.opCfg.targets:
            data = op.getRecording(targetConfig.env)

            if data is None:
                print(f"No recordings available for env {targetConfig.env}, skipping target ...")

                continue

            key = (targetConfig.env, targetConfig.target)

            X, y = self._prepareData(data.entries, targetConfig)

            # No data recorded
            if X is None or y is None:
                continue

            inputData[key] = X
            outputData[key] = y

            for candidate in self._getModelCandidates():
                variant = candidate.calculate(X, y, op, targetConfig.env, targetConfig.target, False)

                allM = allModels.get(key, [])

                allM.append(variant)

                allModels[key] = allM

                if printIntermediate:
                    print(variant.modelType.value + (" (" + variant.metaData["regressor"] + ")" if "regressor" in variant.metaData else "") + ": "
                          + str(round(variant.rmse, 4)) + " [Env: " + str(targetConfig.env.name) + ", Target: " + str(targetConfig.target.name) + "]")

                best = bestModels.get(key)

                if best is None or best.rmse > variant.rmse:
                    bestModels[key] = variant
                    bestCandidates[key] = candidate

        # Now optimize the best models (if possible) after it was found

        for k, v in bestCandidates.items():
            if v.canBeOptimized():
                bestModels[k] = v.calculate(inputData.get(k), outputData.get(k), op, k[0], k[1], True)

        # Visualize the models if required

        for k, v in bestModels.items():
            if visResult is not CostModelVisualization.NONE:
                print("\nBest Model:")
                v.describe()

                X = inputData.get(k)
                y = outputData.get(k)

                if visResult == CostModelVisualization.BEST:
                    v.visualize(op, X, y)
                elif visResult == CostModelVisualization.COMPARISON:
                    v.visualizeComparison(op, allModels[k], X, y)

        # Construct cost model

        model = CostModel()

        for var in bestModels.values():
            print(f"Found {var.modelType.value} ({round(var.rmse, 4)}) for Env: {var.env.name}, Target: {var.target.name}")

            model.addVariant(var)

        return model

    @staticmethod
    def _getModelCandidates():
        candidates: List[CostModelCandidate] = list()

        candidates.append(PolynomialCC(1, 6))

        # candidates.append(GenericCC(SGDRegressor(), True))
        candidates.append(GenericCC(BayesianRidge(), True,
                                    hyperParams={'alpha_init': [1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.9],
                                                 'lambda_init': [1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-9]}))
        candidates.append(GenericCC(Ridge(), True, hyperParams={"alpha": [0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3]}))
        candidates.append(GenericCC(ARDRegression(), True))
        candidates.append(GenericCC(PassiveAggressiveRegressor(), True))
        # candidates.append(GenericCC(TheilSenRegressor(), True)) bugged?
        candidates.append(GenericCC(ElasticNet(), True, hyperParams={"alpha": [0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3]}))

        # candidates.append(GenericCC(SVR(), False))
        # candidates.append(GenericCC(DecisionTreeRegressor(), False))
        # candidates.append(GenericCC(RandomForestRegressor(), False))

        return candidates

    def _cleanData(self, data: List[ExecutionRecording.Entry], targetConfig: CostModelOpCfg.TargetConfig) -> List[ExecutionRecording.Entry]:
        # Does not modify original data array but extracts cleaned data.
        # Remove outliers based on buckets (local cluster every nth elements)

        # Sort list by all cost function params
        data.sort(key=lambda elm: targetConfig.retrieveInputParams(elm))

        def generateBuckets():
            for i in range(0, len(data), self._bucketSize):
                yield data[i:i + self._bucketSize]

        buckets = generateBuckets()

        res = []

        for b in buckets:
            exArrayRaw = [t.getTargetValue(targetConfig.target) for t in b]
            exArray = [t for t in exArrayRaw if t is not None]

            if len(exArray) == 0:
                return []

            # Calculate 50% quantile
            Q3, Q1 = np.percentile(exArray, [75, 25])

            IQR = Q3 - Q1

            lower_limit = Q1 - 1.5 * IQR  # Lower threshold
            upper_limit = Q3 + 1.5 * IQR  # Higher threshold

            for e in b:
                if lower_limit <= e.getTargetValue(targetConfig.target) <= upper_limit:
                    res.append(e)

        return res

    def _prepareData(self, data: List[ExecutionRecording.Entry], targetConfig: CostModelOpCfg.TargetConfig, cleanData: bool = True):
        # Does not modify original data array

        if cleanData:
            data = self._cleanData(data, targetConfig)

            if len(data) == 0:
                return None, None

        targetParam = []

        params: Dict[str, List] = dict()

        for r in data:
            targetParam.append(r.getTargetValue(targetConfig.target))

            for param in targetConfig.inputs:
                pValue = param.recordRetriever(r)
                pName = param.name

                if not isinstance(pValue, (int, float)):
                    printWarning(f"No numeric values detected for feature {pName} ({pValue}), skipping...")

                    return None, None

                if pName in params:
                    params[pName].append(pValue)
                else:
                    params[pName] = [pValue]

        # Transform param data
        for k in params:
            params[k] = np.asarray(params[k]).reshape(len(data), ).tolist()

        total = {**params, **{"y": np.asarray(targetParam).reshape(len(data), )}}  # Merge two dicts
        df = pd.DataFrame(total, index=range(0, len(data)))

        # Split into train and test data
        X = df[params.keys()]
        y = df["y"]

        # Calculate Stats for each param (distribution, min, max, avg, median)

        for i in range(len(targetConfig.inputs)):
            inputParam = targetConfig.inputs[i]

            try:  # Try to gather numeric stats
                data = X.agg({inputParam.name: ['min', 'max', 'mean', 'median', 'std']})

                # Convert stats back to int if the feature column has int values

                if np.issubdtype(X[inputParam.name].dtype, np.integer):
                    data = data.round().astype(int)

                data = list(data.itertuples(name=None, index=False))

                minVal = data[0][0]
                maxVal = data[1][0]
                mean = data[2][0]
                median = data[3][0]
                std = data[4][0]

            except Exception:  # Rely on distribution if no numeric data types
                logging.log(logging.ERROR, traceback.format_exc())
                # Build stats df
                stats_df = X.groupby(inputParam.name)[inputParam.name].agg('count') \
                    .pipe(pd.DataFrame) \
                    .rename(columns={inputParam.name: 'frequency'})

                # Calculate PDF
                stats_df['pdf'] = stats_df['frequency'] / sum(stats_df['frequency'])

                minVal = stats_df['pdf'].idxmin()
                maxVal = stats_df['pdf'].idxmax()
                mean = (stats_df['pdf'] - stats_df['pdf'].mean()).abs().idxmin()  # Closest entry for mean val of pdf
                median = (stats_df['pdf'] - stats_df['pdf'].median()).abs().idxmin()  # Closest entry for median val of pdf
                std = stats_df['pdf'].std()

            inputParam.stats = CostModelFeatureStats(minVal, maxVal, mean, median, std)

        return X, y
