import json
from typing import Optional, List

from spe.pipeline.operators.operator import Operator
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileComputeMode, CompileLanguage, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import InferCustomCodeCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.common.tuple import Tuple
from spe.common.udfCompiler import instantiateUserDefinedFunction


class UDF(Operator):
    def __init__(self, opID: int):
        super(UDF, self).__init__(opID, 0, 0)

        self.rawCode = ""
        self._executable = None

    def setData(self, data: json):
        self.rawCode = data["code"]
        self._executable = instantiateUserDefinedFunction(self, self.rawCode)

        socksIn = data["inputs"]
        socksOut = data["outputs"]

        self._configureSockets(socksIn, socksOut)

    def getData(self) -> dict:
        return {"code": self.rawCode, "inputs": len(self.inputs), "outputs": len(self.outputs)}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        if self._executable is None:  # Error during instantiation, don't override error msg
            return None

        try:
            res = self._executable(tupleIn.data)

            if res is None:
                return self.createSinkTuple()
            elif isinstance(res, tuple):
                return self.createTuple(res)
            else:
                return self.createErrorTuple("Return value is not a tuple!")
        except Exception:
            return self.createErrorTuple()

    # -------------------------- Compilation -------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        return [CompileOpSpecs(CompileFramework.all(),
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=InferCustomCodeCOF(InferCustomCodeCOF.Type.MAP,
                                                                  lambda cfg: self.rawCode,
                                                                  ("input", "$input")))]
