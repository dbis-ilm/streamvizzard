import time
from typing import List, Dict

from spe.pipeline.operators.source import Source
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkStatics import pyFlinkRateLimiterOpDef, \
    pyFlinkRateLimiterOpName
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkUtils import PyFlinkTags
from spe.runtime.compiler.definitions.compileDefinitions import CompileLanguage, CompileComputeMode, CompileFramework, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs


class TextFile(Source):
    def __init__(self,  opID: int):
        super(TextFile, self).__init__(opID, 0, 1)

        self.path = ""
        self.repeat = False
        self.rate = 0
        self.limitRate = False

    def setData(self, data: Dict):
        self.path = data["path"]
        self.repeat = data["repeat"]
        self.rate = max(0, data["rate"])
        self.limitRate = data["limitRate"]

    def getData(self) -> dict:
        return {"path": self.path, "repeat": self.repeat, "rate": self.rate, "limitRate": self.limitRate}

    def _runSource(self):
        init = False

        while self.isRunning():
            if init and not self.repeat:  # To allow dynamic enable / disable of repeat
                time.sleep(0.25)

                continue

            init = True

            try:
                with open(self.path) as file:
                    currentPath = self.path

                    while (line := file.readline()) and self.isRunning():
                        if currentPath != self.path:
                            init = False

                            break

                        line = line.strip()

                        if self.limitRate:
                            sleepDuration = 1 / self.rate

                            if sleepDuration > 1e-3:
                                time.sleep(1 / self.rate)

                        self._produce((line,))

            except Exception:
                self.onExecutionError()

    # -------------------------- Compilation -------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(compileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            assignments = [f"""
                $inDS.from_source(
                    source=fs_{self.getUniqueName()},
                    source_name="{"TextFile_" + str(self.id)}",
                    watermark_strategy=WatermarkStrategy.for_monotonous_timestamps(),
                )"""]

            structDeps = []

            if self.limitRate:
                assignments.append(f"$inDS.map({pyFlinkRateLimiterOpName}({self.rate}))")
                structDeps.append(pyFlinkRateLimiterOpDef)

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.connectors.file_system import FileSource, StreamFormat
            from pyflink.common import WatermarkStrategy""",
                PyFlinkCodeTemplate.Section.FUNCTION_DECLARATION: f"""
            fs_{self.getUniqueName()} = FileSource.for_record_stream_format(
                StreamFormat.text_line_format(),
                "{self.path}"
            ).build()""",
                PyFlinkCodeTemplate.Section.ASSIGNMENTS: assignments},
                structDependencies=structDeps,
                tags=[PyFlinkTags.SOURCE_BOUNDED])

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               [CompileParallelism.SINGLE_NODE, CompileParallelism.DISTRIBUTED],
                               supportedCheck=lambda: not self.repeat,
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.SOURCE, getPyFlinkCode))]
