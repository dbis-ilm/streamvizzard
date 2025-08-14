from typing import Optional

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, max_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures

from analysis.costModel.calculator.costModelCandidate import CostModelCandidate
from analysis.costModel.costModel import CostModelType, CostModelVariant, CostModelTarget, CostModelEnv
from analysis.costModel.operatorEntry import OperatorEntry


class PolynomialCC(CostModelCandidate):
    def __init__(self, minDegree: int, maxDegree: int):
        super(PolynomialCC, self).__init__(True)

        self._minDegree = minDegree
        self._maxDegree = maxDegree

    def calculate(self, X, y, op: OperatorEntry, env: CostModelEnv, target: CostModelTarget, optimize: bool) -> CostModelVariant:
        return self._fitPolynomialRegression(X, y, op, env, target)

    def _fitPolynomialRegression(self, X, y, op: OperatorEntry, env: CostModelEnv, target: CostModelTarget) -> CostModelVariant:
        bestModel: Optional[CostModelVariant] = None

        for i in range(self._minDegree, self._maxDegree + 1):
            model = self._exPolynomialRegression(X, y, op, env, target, i)

            # Only if new value is more than 10% better than old (curse of dimensionality)
            if bestModel is None or (bestModel.rmse != 0 and (model.rmse / bestModel.rmse) < 0.9):
                bestModel = model

        return bestModel

    @staticmethod
    def _exPolynomialRegression(X, y, op: OperatorEntry, env: CostModelEnv, target: CostModelTarget, degree: int) -> CostModelVariant:
        # https://data36.com/polynomial-regression-python-scikit-learn/

        cmTarget = op.getTarget(env, target)

        poly = PolynomialFeatures(degree=degree, include_bias=False)
        poly_features = poly.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(poly_features, y, test_size=0.3, random_state=42)

        # y = ß0 + ß1x1 + ß2x2 + ß3x12 + ß4x22 + ß5x1x2 [for degree 2]
        poly_reg_model = LinearRegression()

        poly_reg_model.fit(X_train, y_train)

        poly_reg_y_predicted = poly_reg_model.predict(X_test)
        poly_reg_rmse = np.sqrt(mean_squared_error(y_test, poly_reg_y_predicted))

        maxError = max_error(y_test, poly_reg_y_predicted)

        # Construct formula
        fNames = poly.get_feature_names_out(poly.feature_names_in_)
        fNames = [f.replace(" ", " * ") for f in fNames]

        formula = target.value + " = " + str(poly_reg_model.intercept_) + " + "

        for i in range(len(fNames)):
            formula += (" + " if i > 0 else "") + str(poly_reg_model.coef_[i]) + " * " + fNames[i]

        return CostModelVariant(env, target, CostModelType.PolynomialRegression, poly_reg_model, poly_reg_rmse, maxError,
                                cmTarget.inputs, metaData={"degree": degree, "formula": formula})
