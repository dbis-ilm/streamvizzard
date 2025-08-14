import numbers
from typing import Optional

import numpy as np

from spe.pipeline.operators.dataCleaning.operators.missingValues import MissingValues
from spe.runtime.advisor.advisorStrategy import AdvisorStrategy, AdvisorStrategyMode
from spe.runtime.advisor.advisorSuggestion import AdvisorSuggestion
from spe.common.tuple import Tuple


class MissingValueStrategy(AdvisorStrategy):
    def __init__(self, operator):
        super(MissingValueStrategy, self).__init__(operator, AdvisorStrategyMode.BEFORE_TUPLE_PROCESSED,
                                                   lambda t: isinstance(t.data[0], dict))

        self._buffer = []

    def registerTuple(self, tupleIn: Tuple):
        self._buffer.append(tupleIn.data[0])

    def makeSuggestion(self, lastTuple: Tuple) -> Optional[AdvisorSuggestion]:
        for data in self._buffer:
            for key in data:
                value = data[key]

                if value is None or (isinstance(value, numbers.Number) and np.isnan(value)):
                    self._buffer.clear()
                    return AdvisorSuggestion([MissingValues], self.operator.getInput(0), "Attribute " + key + " contains missing values!")

        self._buffer.clear()

        return None
    