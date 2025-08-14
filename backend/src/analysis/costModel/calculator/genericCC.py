from typing import Optional, Dict

import numpy as np
from sklearn.metrics import mean_squared_error, max_error
from sklearn.model_selection import GridSearchCV, train_test_split

from analysis.costModel.calculator.costModelCandidate import CostModelCandidate
from analysis.costModel.costModel import CostModelType, CostModelVariant, CostModelTarget, CostModelEnv
from analysis.costModel.operatorEntry import OperatorEntry


class GenericCC(CostModelCandidate):
    def __init__(self, model, hasEquation: bool, hyperParams: Optional[Dict] = None):
        super(GenericCC, self).__init__(hasEquation)

        self._model = model

        self._hyperParams = hyperParams

    def calculate(self, X, y, op: OperatorEntry, env: CostModelEnv, target: CostModelTarget, optimize: bool) -> CostModelVariant:
        cmTarget = op.getTarget(env, target)

        X_train, X_test, y_train, y_test = train_test_split(X.values, y, test_size=0.3, random_state=42)

        if optimize and self._hyperParams is not None:
            # Automatically find the best estimator for defined hyperparameter configurations
            # https://practicaldatascience.co.uk/machine-learning/how-to-use-model-selection-and-hyperparameter-tuning
            gs = GridSearchCV(self._model, self._hyperParams)
            gs.fit(X_train, y_train)

            self._model = gs.best_estimator_

        poly = self._model.fit(X_train, y_train)

        yPredicted = self._model.predict(X_test)

        formula = None

        if self.hasEquation:
            formula = target.value + " = " + str(poly.intercept_[0] if isinstance(poly.intercept_, np.ndarray) else poly.intercept_) + " + "
            for i in range(len(poly.coef_)):
                formula += (" + " if i > 0 else "") + str(poly.coef_[i]) + " * " + X.columns[i]

        mse = mean_squared_error(y_test, yPredicted)
        rmse = np.sqrt(mse)

        maxError = max_error(y_test, yPredicted)

        return CostModelVariant(env, target, CostModelType.GenericRegression, self._model, rmse, maxError,
                                cmTarget.inputs, metaData={"regressor": self._model.__class__.__name__, "formula": formula})

    def canBeOptimized(self) -> bool:
        return self._hyperParams is not None
