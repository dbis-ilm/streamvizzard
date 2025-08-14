from __future__ import annotations

from typing import TYPE_CHECKING

from spe.pipeline.operators.operatorDB import getAdvisorStrategies
from spe.runtime.advisor.advisorStrategy import AdvisorStrategyMode
from spe.runtime.runtimeGateway import getRuntimeManager
from spe.common.timer import Timer
from spe.common.tuple import Tuple
from streamVizzard import StreamVizzard

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator


class OperatorAdvisor:
    def __init__(self, operator: Operator):
        self._advisor = getRuntimeManager().gateway.getAdvisor()
        self._operator = operator

        # Find strategy for operator (can be none)

        self._strategies = getAdvisorStrategies(self._operator)

        # Runtime data

        self._nextAdvisorSuggestion = 0
        self._lastAdvision = None

        # Register listener

        self._operator.getEventListener() \
            .register(self._operator.EVENT_TUPLE_PROCESSED,
                      lambda t, e: self._handleStrategies(t, AdvisorStrategyMode.AFTER_TUPLE_PROCESSED))

        self._operator.getEventListener() \
            .register(self._operator.EVENT_TUPLE_PRE_PROCESSED,
                      lambda t: self._handleStrategies(t, AdvisorStrategyMode.BEFORE_TUPLE_PROCESSED))

    def _handleStrategies(self, tupleIn: Tuple, mode):
        if not self._advisor.isEnabled():
            self._resetAdvisor()

            return

        if self._strategies is not None:
            advise = Timer.currentTime() >= self._nextAdvisorSuggestion

            suggestions = []

            for strategy in self._strategies:
                if strategy.mode != mode or not strategy.shouldHandle(tupleIn):
                    continue

                strategy.registerTuple(tupleIn)

                if advise:
                    suggestion = strategy.makeSuggestion(tupleIn)

                    if suggestion is not None:
                        suggestions.append(suggestion)

            if advise:
                # Send suggestion update - also send zero suggestions in case prev got fixed
                self._lastAdvision = suggestions
                self._advisor.onAdvisorSuggestion(self._operator, suggestions)

                self._nextAdvisorSuggestion = Timer.currentTime() + StreamVizzard.getConfig().ADVISOR_FREQUENCY

    def _resetAdvisor(self):
        # Clear last advision
        if self._lastAdvision is not None:
            self._advisor.onAdvisorSuggestion(self._operator, [])

        self._lastAdvision = None
