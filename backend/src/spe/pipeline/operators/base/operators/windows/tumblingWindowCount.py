from typing import Optional, List, Dict

from spe.pipeline.operators.base.dataTypes.window import Window
from spe.pipeline.operators.base.operators.windows.windowOperator import WindowOperator
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileLanguage, CompileComputeMode, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from spe.runtime.debugger.debuggingUtils import retrieveStoredDTRef
from spe.common.tuple import Tuple


class TumblingWindowCount(WindowOperator):
    def __init__(self, opID: int):
        super(TumblingWindowCount, self).__init__(opID, 1, 1)

        self.value = 0

        self.buffer: List[Tuple] = list()

    def setData(self, data: Dict):
        self.value = int(data["value"])

    def getData(self) -> dict:
        return {"value": self.value}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self.buffer.append(tupleIn)

        if self.isDebuggingEnabled():
            self._onDebugEx(tupleIn)

        if len(self.buffer) >= self.value:
            r = Window(self.buffer)
            self.buffer = []

            return self.createTuple((r,))

        return None

    # ----------------------------- DEBUGGING -----------------------------

    def _onDebugEx(self, tupleIn: Tuple):
        if len(self.buffer) < self.value:  # Only store tuple if it does not complete the buffer
            self._getExecuteDT().registerAttribute("opEx_addedTup", tupleIn.uuid)

    def _onExecutionUndo(self, tup: Tuple):
        addedTup = self.getDebugger().getDT(tup).getAttribute("opEx_addedTup")

        if addedTup is None:  # The undone tuple completed the buffer, restore buffer from result tuple
            winData: Window = tup.data[0]
            self.buffer = winData.getTuples().copy()

        self.buffer.pop()

    def _onExecutionRedo(self, tup: Tuple):
        addedTup = self.getDebugger().getDT(tup).getAttribute("opEx_addedTup")

        if addedTup is not None:
            inputDt = retrieveStoredDTRef(self, tup, "opEx_addedTup")

            if inputDt is not None:
                self.buffer.append(inputDt.getTuple(True))

        else:  # Tuple to redo completed the buffer
            self.buffer.clear()

    # -------------------------- Compilation -------------------------

    def deriveOutThroughput(self, inTp: float):
        return inTp / self.value

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(cfg: OpCompileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.window import CountTumblingWindowAssigner""",
                PyFlinkCodeTemplate.Section.ASSIGNMENTS:
                    self._getPyFlinkCompileAssignment(f"CountTumblingWindowAssigner.of({self.value})", cfg.parallelismCount)})

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.WINDOW, getPyFlinkCode))]
