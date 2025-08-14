import json
from typing import Optional, List

from spe.common.serialization.jsonSerialization import deserializeFromJSON
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkStatics import pyFlinkJSONDeserializer
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileLanguage, CompileComputeMode, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs


class ParseJSON(Operator):
    """
    Inputs: 1
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(ParseJSON, self).__init__(opID, 1, 1)

    def setData(self, data: json):
        pass

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        return self.createTuple((deserializeFromJSON(tupleIn.data[0]),))

    # -------------------------- Compilation -------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(_):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.FUNCTION_CONTENT: f"""
            return {pyFlinkJSONDeserializer}($input[0])"""})

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.MAP, getPyFlinkCode))]
