import json
from typing import Optional, List

from spe.pipeline.operators.base.operators.windows.windowProcessor import WindowProcessor
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileComputeMode, \
    CompileParallelism, CompileLanguage
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.common.tuple import Tuple
from spe.runtime.compiler.opCompileConfig import OpCompileConfig


class WindowCollect(WindowProcessor):
    def __init__(self, opID: int):
        super(WindowCollect, self).__init__(opID, 1, 1)

    def setData(self, data: json):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        window = tupleIn.data[0]

        return self.createTuple((window.toDataArray(),))

    # -------------------------- Compilation -------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(cfg: OpCompileConfig):
            return self._getPyFlinkProcessorFunc(cfg.parallelismCount, "yield list(elements)")

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.OTHER, getPyFlinkCode))]
