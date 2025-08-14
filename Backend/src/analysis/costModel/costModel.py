from __future__ import annotations

import logging
import os.path
from enum import Enum
from typing import Dict, List, Any, Type, Optional, TYPE_CHECKING, Union

import dill as dill
import numpy as np
from matplotlib import pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures

from utils.fileUtils import getStructuredOperatorPath
from analysis.costModel.configurations.costModelOpSetups import OpParamFeature, OpInputDataFeature, OpMetaDataFeature

if TYPE_CHECKING:
    from analysis.costModel.operatorEntry import OperatorEntry
    from analysis.costModel.configurations.costModelOpSetups import CostModelFeature
    from spe.pipeline.operators.operator import Operator


class CostModelEnv(Enum):
    """
    Environment utilized for recording data points for the costModel calculation.
    By default, operators are executed and recorded using the StreamVizzard system.
    Externally provided data can declare different environments, such as JavaCPU.
    """

    SV_CPU = "SvCPU"


class CostModelTarget(Enum):
    """ PredictionTarget of the costModel. """

    EXECUTION_TIME = "ExecutionTime"  # In s
    OUTPUT_SIZE = "OutputSize"  # In bytes


class CostModelType(Enum):
    PolynomialRegression = "Polynomial Regression"
    GenericRegression = "Generic Regression"


class CostModelMetaData:
    """ Various meta information provided externally for the model prediction. """

    class Param(Enum):
        INPUT_DATA_SIZE = "inputDataSize"  # Size of the input tuple
        # Future Work: Could also retrieve system stats (CPU clock speed, ...)

    def __init__(self, inputDataSize: int):
        self.metaData: Dict[CostModelMetaData.Param, Any] = dict()

        self.metaData[CostModelMetaData.Param.INPUT_DATA_SIZE] = inputDataSize

    def get(self, param: Param):
        return self.metaData.get(param)

    @staticmethod
    def construct(inputDataSize: int) -> CostModelMetaData:
        # More extractions (also automated extractions from the system) can be added here

        return CostModelMetaData(inputDataSize)


class CostModelVariant:
    """ A costModel variant reflects a calculated model for a specific CostModelTarget and CostModelEnv. """

    def __init__(self, env: CostModelEnv, target: CostModelTarget, modelType: CostModelType,
                 model, rmse: float, maxError: float, features: List[CostModelFeature], metaData: Dict):
        self.env = env
        self.target = target

        self.modelType = modelType
        self.model = model

        self.features = features  # Input parameters

        self.metaData = metaData

        # Model quality metrics

        self.rmse = rmse  # Root-mean-square deviation (standard deviation)
        self.maxError = maxError  # Maximum residual error

    def predict(self, operator: Optional[Operator], inData: Optional[tuple], metaData: CostModelMetaData) -> Any:
        """
        Extracts values for the model features from the (optionally) provided operator and data tuple
        and performs a single model data prediction. If no operator or data is provided, the avg values
        from the training data are utilized.
        """

        inputVec = []

        for feat in self.features:
            if isinstance(feat, OpParamFeature):
                # Retrieves the requested param from the operator instance.
                # If no operator instance is available, take the avg values from the trained data

                if operator is not None:
                    param = feat.retriever(operator)
                else:
                    param = feat.stats.avg

            elif isinstance(feat, OpInputDataFeature):
                # Retrieves the requested param from the input data tuple.
                # If no data tuple is available, take the avg values from the trained data

                if inData is not None:
                    param = feat.retriever(inData)
                else:
                    param = feat.stats.avg
            elif isinstance(feat, OpMetaDataFeature):
                # Retrieves the requested param from the provided meta-data.

                param = feat.retriever(metaData)
            else:
                continue

            inputVec.append(param)

        return self.predictRaw(inputVec)[0]

    def predictRaw(self, inputVal: Union[List[Any], List[List[Any]]]) -> Any:
        """
        Predicts one output data value for each input feature array.
        """

        inputArray = np.asarray(inputVal)

        # Future Work: Could support different types of models with different types of prediction functionality

        return self.model.predict(self._transformInput(inputArray.reshape(-1, len(self.features))))

    def _transformInput(self, modelInput):
        if self.modelType == CostModelType.PolynomialRegression:
            poly = PolynomialFeatures(degree=self.metaData["degree"], include_bias=False)
            poly_features = poly.fit_transform(modelInput)
            return poly_features
        else:
            return modelInput

    def getFormula(self) -> Optional[str]:
        """ Returns the mathematical formula of this model (if available). """

        return self.metaData.get("formula", None)

    def describe(self):
        res = ""

        if self.modelType == CostModelType.PolynomialRegression:
            res = self.modelType.value
            res += "\nDegree: " + str(self.metaData["degree"])
        elif self.modelType == CostModelType.GenericRegression:
            res = self.modelType.value + " (" + self.metaData["regressor"] + ")"

        res += "\nRMSE: " + str(self.rmse) + ", MaxError: " + str(self.maxError)

        if self.metaData["formula"] is not None:
            res += "\nFormula: " + self.metaData["formula"]

        print(res)

    def visualize(self, op: OperatorEntry, X, y, testSize: float = 0.3, maxDataPoints: int = 2500):
        # Downsample data for performance reasons
        X = X.sample(n=min(maxDataPoints, len(X)), random_state=42)
        y = y.sample(n=min(maxDataPoints, len(y)), random_state=42)

        # Extract test values
        _, X_test, _, _ = train_test_split(X.values, y, test_size=testSize, random_state=42)

        # Predict values
        yPredicted = self.predictRaw(X_test)

        features = len(self.features)

        if features > 1:
            fig, axes = plt.subplots(nrows=1, ncols=features, figsize=(12, 6))

            for feat in range(features):
                featName = self.features[feat].name

                axes[feat].scatter(X[featName], y, label="Recorded")
                axes[feat].set_title(featName)

                axes[feat].scatter(X_test[:, feat], yPredicted, c="red", label="Predicted")

                axes[feat].legend()
        else:
            plt.figure(figsize=(12, 6))

            plt.scatter(X, y, label="Recorded")
            plt.title(self.features[0].name)

            plt.scatter(X_test[:, 0], yPredicted, c="red", label="Predicted")

        if self.modelType == CostModelType.PolynomialRegression:
            modelDescr = self.modelType.value + " [Degree: " + str(self.metaData["degree"]) + "]"
        else:
            modelDescr = self.metaData["regressor"]

        plt.suptitle(f"Visualization of impact of model features for {op.opCfg.operator.getName()} operator.\n"
                     f"Model: {modelDescr}, Environment: {self.env.name}, Target: {self.target.name}")
        plt.ylabel(self.target.value)
        plt.get_current_fig_manager().set_window_title(op.opCfg.operator.getName() + " > " + modelDescr)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def visualizeComparison(self, op: OperatorEntry, otherModels: List[CostModelVariant], X, y,
                            testSize: float = 0.3, maxDataPoints: int = 2500):
        # Downsample data for performance reasons
        X = X.sample(n=min(maxDataPoints, len(X)), random_state=42)
        y = y.sample(n=min(maxDataPoints, len(y)), random_state=42)

        # Extract test values
        _, X_test, _, _ = train_test_split(X.values, y, test_size=testSize, random_state=42)

        # Predict values for all models
        yPredicted = self.predictRaw(X_test)
        yPredictedOther = []

        for mod in otherModels:
            if mod != self:
                yPredictedOther.append((mod, mod.predictRaw(X_test)))

        features = len(self.features)

        dataSetCol = "#277DA1"
        bestCol = "#F94144"
        # bestCol = "#de425b"
        colList = ["#9565B5", "#8F4C77", "#43AA8B", "#90BE6D", "#F9C74F", "#F9844A", "#F8961E", "#F3722C"]
        # colList = ["#488f31", "#7ba440", "#a9b855", "#d5cc6f", "#ffe18d", "#fabb6d", "#f29459", "#e66a51"]
        colCounter = 0

        def getColor():
            nonlocal colCounter
            col = colList[colCounter]
            colCounter += 1

            if colCounter >= len(colList):
                colCounter = 0

            return col

        if features > 1:
            fig, axes = plt.subplots(nrows=1, ncols=features, figsize=(12, 6))

            for feat in range(features):
                featName = self.features[feat].name

                axes[feat].scatter(X[featName], y, s=5, c=dataSetCol, label="Recorded")
                axes[feat].set_title(featName)

                # Plot others
                for e in yPredictedOther:
                    yPred = e[1]
                    mod = e[0]

                    name = mod.metaData["regressor"] if "regressor" in mod.metaData else mod.modelType.value
                    axes[feat].scatter(X_test[:, feat], yPred, c=getColor(), s=5, label=name + " | RMSE: " + str(round(mod.rmse, 3)))

                # Plot best
                bestName = self.metaData["regressor"] if "regressor" in self.metaData else self.modelType.value
                axes[feat].scatter(X_test[:, feat], yPredicted, c=bestCol, s=10, label=bestName + " | RMSE: " + str(round(self.rmse, 3)))

                axes[feat].legend()
        else:
            plt.figure(figsize=(12, 6))

            plt.title(self.features[0].name)

            plt.scatter(X, y, s=5, c=dataSetCol, label="Recorded")

            # Plot others
            for e in yPredictedOther:
                yPred = e[1]
                mod = e[0]

                name = mod.metaData["regressor"] if "regressor" in mod.metaData else mod.modelType.value

                plt.scatter(X_test[:, 0], yPred, c=getColor(), s=5, label=name + " | RMSE: " + str(round(mod.rmse, 3)))

            # Plot best
            bestName = self.metaData["regressor"] if "regressor" in self.metaData else self.modelType.value
            plt.scatter(X_test[:, 0], yPredicted, c=bestCol, s=10, label=bestName + " | RMSE: " + str(round(self.rmse, 3)))

        if self.modelType == CostModelType.PolynomialRegression:
            modelDescr = self.modelType.value + " [Degree: " + str(self.metaData["degree"]) + "]"
        else:
            modelDescr = self.metaData["regressor"]

        plt.suptitle(f"Comparison of model feature impact for all candidates for {op.opCfg.operator.getName()} operator.\n"
                     f"BestModel: {modelDescr}, Environment: {self.env.name}, Target: {self.target.name}")
        plt.legend(loc="lower right")
        plt.ylabel(self.target.value)
        plt.get_current_fig_manager().set_window_title(op.opCfg.operator.getName() + " > " + modelDescr)
        plt.legend()
        plt.tight_layout()
        plt.show()


class CostModel:
    """
    An operator costModel that may contain multiple CostModelVariants with different prediction targets and environments.
    """

    def __init__(self):
        self._variants: List[CostModelVariant] = list()

    def addVariant(self, variant: CostModelVariant):
        self._variants.append(variant)

    def getVariant(self, env: CostModelEnv, target: CostModelTarget):
        for var in self._variants:
            if var.env == env and var.target == target:
                return var

        return None

    def save(self, operator: Type[Operator], rootPath: str):
        parent, opName = getStructuredOperatorPath(operator, rootFolder=rootPath, mkdirs=True)

        dill.dump(self, open(os.path.join(parent, opName + ".svcm"), 'wb'))

    @staticmethod
    def load(operator: Type[Operator], rootPath: str):
        parent, opName = getStructuredOperatorPath(operator, rootFolder=rootPath)

        loadPath = os.path.join(parent, opName + ".svcm")

        if not os.path.exists(loadPath):
            return None

        try:
            cm: CostModel = dill.load(open(loadPath, 'rb'))

            return cm
        except Exception:
            logging.log(logging.ERROR, "Couldn't load CostModel at path: " + loadPath)

            return None
