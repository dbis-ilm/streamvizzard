import json
from typing import Optional, List

from spe.pipeline.operators.base.operators.windows.windowProcessor import WindowProcessor
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileComputeMode, \
    CompileParallelism, CompileLanguage
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.common.tuple import Tuple


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
        # ProcessAllWindowFunction only for non-keyed streams, for keyed: ProcessWindowFunction,
        # but apparently not possible to collect all data into one list again ... only per key

        def getPyFlinkCode(compileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.functions import ProcessAllWindowFunction""",
                PyFlinkCodeTemplate.Section.FUNCTION_DECLARATION: f"""
            class ProcessAll{self.getUniqueName().replace("_", "")}(ProcessAllWindowFunction):
                def process(self, _, elements):
                    yield list(elements)
            """,
                PyFlinkCodeTemplate.Section.ASSIGNMENTS: f"""
            $inDS.process(ProcessAll{self.getUniqueName().replace("_", "")}())"""})

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.OTHER, getPyFlinkCode))]
