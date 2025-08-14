from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Optional, Callable

from spe.runtime.advisor.advisorSuggestion import AdvisorSuggestion
from spe.common.tuple import Tuple

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator


class AdvisorStrategyMode(Enum):
    BEFORE_TUPLE_PROCESSED = 1
    AFTER_TUPLE_PROCESSED = 2


class AdvisorStrategy(ABC):
    def __init__(self, operator: Operator, mode: AdvisorStrategyMode, dataTypeCheck: Optional[Callable[[Tuple], bool]] = None):
        self.operator = operator
        self.mode: AdvisorStrategyMode = mode
        self.dataTypeCheck = dataTypeCheck

    def shouldHandle(self, tupleIn: Tuple):
        return self.dataTypeCheck(tupleIn) if self.dataTypeCheck is not None else True

    @abstractmethod
    def registerTuple(self, tupleIn: Tuple):
        ...

    @abstractmethod
    def makeSuggestion(self, lastTuple: Tuple) -> Optional[AdvisorSuggestion]:
        ...
