from typing import Optional

from spe.pipeline.operators.imageProc.operators.transform.convert import Convert
from spe.runtime.advisor.advisorStrategy import AdvisorStrategy, AdvisorStrategyMode
from spe.runtime.advisor.advisorSuggestion import AdvisorSuggestion
from spe.common.tuple import Tuple


class GrayInputStrategy(AdvisorStrategy):
    def __init__(self, operator):
        super(GrayInputStrategy, self).__init__(
            operator, AdvisorStrategyMode.BEFORE_TUPLE_PROCESSED)

    def registerTuple(self, tupleIn: Tuple):
        pass

    def makeSuggestion(self, lastTuple: Tuple) -> Optional[AdvisorSuggestion]:
        if not lastTuple.data[0].isGrey():
            return AdvisorSuggestion([Convert], self.operator.getInput(0), "A grayscale input image is required!")

        return None
