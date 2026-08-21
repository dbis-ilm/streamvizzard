from typing import Optional, List, Dict

from spe.pipeline.operators.base.dataTypes.window import Window
from spe.pipeline.operators.base.operators.windows.windowOperator import WindowOperator
from spe.common.tuple import Tuple
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileLanguage, CompileComputeMode, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from spe.runtime.debugger.debuggingUtils import retrieveStoredDTRef


class SlidingWindowCount(WindowOperator):
    def __init__(self, opID: int):
        super(SlidingWindowCount, self).__init__(opID, 1, 1)

        self.count = 0
        self.slide = 0

        self._buffer: List[Tuple] = list()

    def setData(self, data: Dict):
        self.count = int(data["count"])
        self.slide = min(self.count, int(data["slide"]))

    def getData(self) -> dict:
        return {"count": self.count, "slide": self.slide}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self._buffer.append(tupleIn)

        if self.isDebuggingEnabled():
            self._onDebugEx(tupleIn)

        if len(self._buffer) >= self.count:
            r = Window(self._buffer)

            self._buffer = self._buffer[self.slide:]

            return self.createTuple((r,))

        return None

    # ----------------------------- DEBUGGING -----------------------------

    def _onDebugEx(self, tupleIn: Tuple):
        self._getExecuteDT().registerAttribute("opEx_addedTup", tupleIn.uuid)

    def _onExecutionUndo(self, tup: Tuple):
        # Tuple to undo produced a window, restore the buffer to undo this

        if len(tup.data) == 1 and isinstance(tup.data[0], Window):
            winData = tup.data[0]
            self._buffer = winData.getTuples().copy()

        self._buffer.pop()

    def _onExecutionRedo(self, tup: Tuple):
        inputDt = retrieveStoredDTRef(self, tup, "opEx_addedTup")

        if inputDt is not None:
            self._buffer.append(inputDt.getTuple(True))

        if len(self._buffer) >= self.count:
            self._buffer = self._buffer[self.slide:]

    # -------------------------- Compilation -------------------------

    def deriveOutThroughput(self, inTp: float):
        return inTp / self.slide

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(cfg: OpCompileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.window import CountSlidingWindowAssigner""",
                PyFlinkCodeTemplate.Section.ASSIGNMENTS:
                    self._getPyFlinkCompileAssignment(f"CountSlidingWindowAssigner.of({self.count}, {self.slide})", cfg.parallelismCount)})

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.WINDOW, getPyFlinkCode))]
