from typing import Optional

from spe.runtime.advisor.advisorStrategy import AdvisorStrategy, AdvisorStrategyMode
from spe.runtime.advisor.advisorSuggestion import AdvisorSuggestion
from spe.common.tuple import Tuple


class AnomalyValueStrategy(AdvisorStrategy):
    def __init__(self, operator):
        super(AnomalyValueStrategy, self).__init__(operator, AdvisorStrategyMode.BEFORE_TUPLE_PROCESSED,
                                                   lambda t: isinstance(t.data[0], dict))
        self.list_hold = []
        self.hold = []
        self.register = self.registerTuple

    def registerTuple(self, tupleIn: Tuple):
        pass

    def makeSuggestion(self, lastTuple: Tuple) -> Optional[AdvisorSuggestion]:
        # return AdvisorSuggestion([AnomalyDetection], self.operator.getInput(0), "A Missing Value Operator Is Required")

        return None
