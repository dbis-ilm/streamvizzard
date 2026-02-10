import textwrap
from abc import ABC
from string import Template

from spe.pipeline.operators.operator import Operator
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate
from spe.runtime.compiler.definitions.compileOpMetaData import CompileOpMetaData


class WindowProcessor(Operator, ABC):
    @property
    def allowedParents(self):
        from spe.pipeline.operators.base.operators.windows.windowOperator import WindowOperator
        return [WindowOperator]

    def getCompileMetaData(self) -> CompileOpMetaData:
        # Formally, the processor could have a different level of parallelism compare to the window operator.
        # For simplicity during placement and compilation (cant serialize window) we enforce the same target here.
        return CompileOpMetaData(inheritTarget=True)

    # -------------------------- Compilation -------------------------

    def _getPyFlinkProcessorFunc(self, parallelism: int, funcContent: str, contentImports: str = None) -> PyFlinkCodeTemplate:
        # window_all for non-keyed streams with para=1, else we need a keyed window

        if parallelism == 1:
            imports = "from pyflink.datastream.functions import ProcessAllWindowFunction"
            code = Template(textwrap.dedent(f"""
            class Process{self.getUniqueName().replace("_", "")}(ProcessAllWindowFunction):
                def process(self, _, elements):
                    $content
            """))
        else:
            imports = "from pyflink.datastream.functions import ProcessWindowFunction"
            code = Template(textwrap.dedent(f"""
            class Process{self.getUniqueName().replace("_", "")}(ProcessWindowFunction):
                def process(self, key, _, elements):
                    $content
            """))

        if contentImports is not None:
            imports = imports + "\n" + contentImports

        finalCode = code.substitute(content=funcContent.strip())

        # If parallelized window, rebalance the stream to ensure an even load-balancing (usually low impact since window is executed rarely)
        # -> If reworked, adjust also in frameworkAdvisor:adviceCanChain

        pyFlinkCode = PyFlinkCodeTemplate({
            PyFlinkCodeTemplate.Section.IMPORTS: imports,
            PyFlinkCodeTemplate.Section.FUNCTION_DECLARATION: finalCode,
            PyFlinkCodeTemplate.Section.ASSIGNMENTS: f"""
        $inDS.process(Process{self.getUniqueName().replace("_", "")}())"""})

        return pyFlinkCode
