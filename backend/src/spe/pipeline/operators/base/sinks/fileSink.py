import asyncio
import os

from typing import Optional, Dict, List, TextIO

from spe.pipeline.operators.sink import Sink
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileLanguage, CompileComputeMode, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.common.tuple import Tuple


class FileSink(Sink):
    def __init__(self, opID: int):
        super().__init__(opID, 1)

        self.path = ""

        self._file: Optional[TextIO] = None

    def setData(self, data: Dict):
        changed = self.path != data["path"]

        self.path = data["path"]

        if changed:
            self._openFile()

    def getData(self) -> dict:
        return {"path": self.path}

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super().onRuntimeCreate(eventLoop)

        self._openFile()

    def onRuntimeDestroy(self):
        super().onRuntimeDestroy()

        self._closeFile()

    def _openFile(self):
        if self._file is not None:
            self._closeFile()

        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)

            self._file = open(self.path, "w", buffering=1)
        except Exception:
            self.onExecutionError()

    def _closeFile(self):
        if self._file is not None:
            self._file.close()

            self._file = None

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        if self._file is None:
            return None  # Error opening file

        try:
            self._file.write(str(tupleIn.data[0]) + "\n")
            self._file.flush()
        except Exception:
            return self.createErrorTuple()

        return self.createSinkTuple()

    # -------------------------- Compilation -------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(compileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            name, extension = os.path.splitext(os.path.basename(self.path))

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.connectors.file_system import FileSink, OutputFileConfig
            from pyflink.common import Encoder""",
                PyFlinkCodeTemplate.Section.FUNCTION_DECLARATION: f"""
            fs_{self.getUniqueName()} = FileSink \\
                .for_row_format(\"{os.path.dirname(self.path)}\", Encoder.simple_string_encoder()) \\
                .with_output_file_config(OutputFileConfig.builder().with_part_prefix(\"{name}\").with_part_suffix(\"{extension}\").build()) \\
                .build()""",
                PyFlinkCodeTemplate.Section.ASSIGNMENTS: f"""$inDS.sink_to(fs_{self.getUniqueName()})"""})

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.SINK, getPyFlinkCode))]
