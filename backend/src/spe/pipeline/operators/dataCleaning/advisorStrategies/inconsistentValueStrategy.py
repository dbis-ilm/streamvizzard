from typing import Optional

from spe.runtime.advisor.advisorStrategy import AdvisorStrategy, AdvisorStrategyMode
from spe.runtime.advisor.advisorSuggestion import AdvisorSuggestion
from spe.common.tuple import Tuple


class InconsistentValueStrategy(AdvisorStrategy):
    def __init__(self, operator):
        super(InconsistentValueStrategy, self).__init__(operator, AdvisorStrategyMode.BEFORE_TUPLE_PROCESSED,
                                                   lambda t: isinstance(t.data[0], dict))

    def registerTuple(self, tupleIn: Tuple):
        pass

    def makeSuggestion(self, lastTuple: Tuple) -> Optional[AdvisorSuggestion]:
        # return AdvisorSuggestion([Inconsistency], self.operator.getInput(0), "A Inconsistent Value Operator Is Required")

        return None
