import json
import time
from typing import List

from spe.common.timer import Timer
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

    def setData(self, data: json):
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

                    startTime = Timer.currentRealTime()
                    counter = 0

                    while line := file.readline():
                        if not self.isRunning() \
                                or currentPath != self.path:
                            break

                        line = line.strip()

                        if self.limitRate and self.rate > 0:
                            # Compensates inaccuracies in sleeps by fixed produce 'clock'
                            nextProduceTime = startTime + counter * (1.0 / self.rate)

                            sleepDuration = nextProduceTime - Timer.currentRealTime()

                            if sleepDuration > 1e-3:
                                time.sleep(sleepDuration)

                        self._produce((line,))

                        counter += 1

            except Exception:
                self.onExecutionError()

    # -------------------------- Compilation -------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def verifyFlinkCompatibility() -> bool:
            # Repeat not supported

            return not self.repeat

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
                               supportedCheck=verifyFlinkCompatibility,
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.SOURCE, getPyFlinkCode))]
