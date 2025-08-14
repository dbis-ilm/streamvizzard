from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from analysis.costModel.costModel import CostModel, CostModelEnv, CostModelTarget, CostModelVariant, CostModelMetaData
from spe.runtime.compiler.definitions.compileDefinitions import CompileLanguage, CompileComputeMode, CompileFramework
from spe.runtime.compiler.placement.knowledgeProvider.opKnowledgeProvider import \
    OpKnowledgeProvider, OpKnowledgeType

if TYPE_CHECKING:
    from spe.runtime.compiler.opCompileData import OpCompileData
    from spe.runtime.monitor.pipelineDataAnalyzer import OperatorDataAnalysis


class CostModelKP(OpKnowledgeProvider):
    def __init__(self, opData: OpCompileData):
        super().__init__(OpKnowledgeType.COST_MODEL, opData)

        # The CostModel are dependent on the language and compute mode
        # Framework and parallelism shouldn't play a role for performance measurements

        self._cmPath: Optional[str] = None

        self._costModel: Optional[CostModel] = None  # Lazy load

    def _updateCMPath(self, newCmPath: str):
        if self._cmPath is not None and self._cmPath != newCmPath:
            self._costModel = None  # Reset cache

        self._cmPath = newCmPath

    def _getCostModel(self, cmFolder: str, framework: CompileFramework, language: CompileLanguage, computeMode: CompileComputeMode) -> Optional[CostModelVariant]:
        self._updateCMPath(cmFolder)

        if self._costModel is None:
            self._costModel = CostModel.load(type(self.opData.operator), self._cmPath)

        if self._costModel is not None:
            # Map language/computeMode to CostModel env

            targetEnv = None

            if language == CompileLanguage.PYTHON and computeMode == CompileComputeMode.CPU:
                targetEnv = CostModelEnv.SV_CPU

            if targetEnv is None:
                return None

            return self._costModel.getVariant(targetEnv, CostModelTarget.EXECUTION_TIME)

        return None

    def predictExecutionTime(self, cmFolder: str, framework: CompileFramework, language: CompileLanguage,
                             computeMode: CompileComputeMode, exStats: Optional[OperatorDataAnalysis]) -> Optional[float]:
        variant = self._getCostModel(cmFolder, framework, language, computeMode)

        if variant is not None:
            # Future Work: Provide information about the input data tuple for better predictions [from execution stats]

            cmMetaData = CostModelMetaData.construct(int(exStats.inDataSizeStats.average) if exStats is not None else 0)

            return max(0, variant.predict(self.opData.operator, None, cmMetaData))

        return None
