from typing import Optional, List

from spe.pipeline.operators.dataCleaning.operators.missingValues import MissingValues
from spe.runtime.advisor.advisorStrategy import AdvisorStrategy, AdvisorStrategyMode
from spe.runtime.advisor.advisorSuggestion import AdvisorSuggestion, AddOpAS
from spe.common.tuple import Tuple


class MissingValueStrategy(AdvisorStrategy):
    def __init__(self, operator):
        super(MissingValueStrategy, self).__init__(operator, AdvisorStrategyMode.BEFORE_TUPLE_PROCESSED,
                                                   lambda t: isinstance(t.data[0], list))

    def registerTuple(self, tupleIn: Tuple):
        pass

    def makeSuggestion(self, lastTuple: Tuple) -> Optional[List[AdvisorSuggestion]]:
        for data in lastTuple.data[0]:
            if data is None:
                return [AddOpAS([AddOpAS.OpConfig(MissingValues, {"mode": "drop"})],
                                self.operator.getInput(0), "Data contains missing values, unsupported by this operator!")]

        return None
    