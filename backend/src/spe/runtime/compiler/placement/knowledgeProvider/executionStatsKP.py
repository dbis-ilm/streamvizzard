from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from spe.runtime.compiler.placement.knowledgeProvider.opKnowledgeProvider import \
    OpKnowledgeProvider, OpKnowledgeType
from spe.runtime.monitor.pipelineDataAnalyzer import PipelineDataAnalyzer

if TYPE_CHECKING:
    from spe.runtime.compiler.opCompileData import OpCompileData
    from spe.runtime.monitor.pipelineDataAnalyzer import OperatorDataAnalysis


class ExecutionStatsKP(OpKnowledgeProvider):
    def __init__(self, opData: OpCompileData):
        super().__init__(OpKnowledgeType.EXECUTION_STATS, opData)

        self.opStats: Optional[OperatorDataAnalysis] = None
        self.operatorUUID: Optional[str] = None

    def getStats(self) -> Optional[OperatorDataAnalysis]:
        # Cache the operator stats and only reload if the operatorUUID changes (e.g. initially)

        if self.operatorUUID != self.opData.operator.uuid:
            self.operatorUUID = self.opData.operator.uuid

            self.opStats = PipelineDataAnalyzer.loadOperatorData(self.operatorUUID)

        return self.opStats
