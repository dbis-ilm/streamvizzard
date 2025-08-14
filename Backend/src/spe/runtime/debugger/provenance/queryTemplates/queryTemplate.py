from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Optional, Dict

from py2neo.cypher import Cursor

from spe.runtime.debugger.debugStep import DebugStep

if TYPE_CHECKING:
    from spe.runtime.debugger.provenance.provenanceInspector import ProvenanceInspector


class QueryTarget(Enum):
    FIND_OPTIMUM = "Optimum"
    UPDATE_IMPACT = "UpdateImpact"

    @staticmethod
    def parse(val: str) -> Optional[QueryTarget]:
        for k in QueryTarget:
            if val == k.value:
                return k

        return None


class QueryOpTargetType(Enum):
    METRIC = "Metric"
    PARAM = "Param"

    @staticmethod
    def parse(val: str) -> Optional[QueryOpTargetType]:
        for k in QueryOpTargetType:
            if val == k.value:
                return k

        return None


class QueryTemplate(ABC):
    def __init__(self, targetType: QueryTarget, inputData):
        self.targetType = targetType
        self.inputData = inputData

    @staticmethod
    def getTemplateForTarget(target: QueryTarget, inputData) -> Optional[QueryTemplate]:
        if target == QueryTarget.FIND_OPTIMUM:
            from spe.runtime.debugger.provenance.queryTemplates.findOptimumQT import FindOptimumQT
            return FindOptimumQT(inputData)
        elif target == QueryTarget.UPDATE_IMPACT:
            from spe.runtime.debugger.provenance.queryTemplates.updateImpactQT import UpdateImpactQT
            return UpdateImpactQT(inputData)

        return None

    @abstractmethod
    def generateQuery(self) -> str:
        pass

    @abstractmethod
    def extractResult(self, inspector: ProvenanceInspector, result: Cursor) -> Dict:
        ...

    @staticmethod
    def _receiveStep(branchID: int, stepID: int, inspector: ProvenanceInspector) -> Optional[DebugStep]:
        branch = inspector.getDebugger().getHistory().getBranch(branchID)

        if branch is None:
            return None

        return branch.getStep(stepID)
