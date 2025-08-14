from __future__ import annotations
import abc
from enum import Enum
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from spe.runtime.compiler.opCompileData import OpCompileData


class OpKnowledgeType(Enum):
    COST_MODEL = 0,
    EXECUTION_STATS = 1


class OpKnowledgeProvider(abc.ABC):
    def __init__(self, knowledgeType: OpKnowledgeType, opData: OpCompileData):
        self.knowledgeType = knowledgeType
        self.opData = opData

    @staticmethod
    def requestAll(opData: OpCompileData) -> Dict[OpKnowledgeType, OpKnowledgeProvider]:
        """
        Tries to register all knowledge provider for this operator.
        Specific provider might not be registered, if no knowledge is available for them.
        """

        res = dict()

        from spe.runtime.compiler.placement.knowledgeProvider.costModelKP import CostModelKP
        from spe.runtime.compiler.placement.knowledgeProvider.executionStatsKP import ExecutionStatsKP

        possibleKP = [CostModelKP, ExecutionStatsKP]

        for kp in possibleKP:
            kpInst = kp(opData)

            res[kpInst.knowledgeType] = kpInst

        return res
