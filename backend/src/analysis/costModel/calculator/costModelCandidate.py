from abc import ABC, abstractmethod

from analysis.costModel.costModel import CostModelVariant, CostModelTarget, CostModelEnv
from analysis.costModel.operatorEntry import OperatorEntry


class CostModelCandidate(ABC):
    def __init__(self, hasEquation: bool):
        self.hasEquation = hasEquation

    @abstractmethod
    def calculate(self, X, y, op: OperatorEntry, env: CostModelEnv, target: CostModelTarget, optimize: bool) -> CostModelVariant:
        pass

    def canBeOptimized(self) -> bool:
        return False
