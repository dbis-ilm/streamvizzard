import json
from typing import Optional, List

from spe.pipeline.operators.operator import Operator
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileComputeMode, \
    CompileParallelism, CompileLanguage
from spe.runtime.compiler.definitions.compileOpFunction import InferCustomCodeCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.common.tuple import Tuple
from spe.common.udfCompiler import instantiateUserDefinedFunction


class Filter(Operator):
    def __init__(self, opID: int):
        super(Filter, self).__init__(opID, 1, 1)

        self.rawCode = ""
        self._executable = None

    def setData(self, data: json):
        self.rawCode = data["code"]

        self._executable = instantiateUserDefinedFunction(self, self.rawCode)

    def getData(self) -> dict:
        return {"code": self.rawCode}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        if self._executable is None:  # Error during instantiation, don't override error msg
            return None

        try:
            res = self._executable(tupleIn.data)

            if res is not None and res:
                return self.createTuple(tupleIn.data)
            else:
                return self.createSinkTuple()
        except Exception:
            return self.createErrorTuple()

    # -------------------------- Compilation -------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        return [CompileOpSpecs(CompileFramework.all(),
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=InferCustomCodeCOF(InferCustomCodeCOF.Type.FILTER,
                                                                  lambda cfg: self.rawCode,
                                                                  ("input", "$input")))]
