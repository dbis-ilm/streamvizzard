import asyncio
import json
from threading import Timer
from typing import Optional, List

from spe.pipeline.operators.base.dataTypes.window import Window
from spe.pipeline.operators.base.operators.windows.windowOperator import WindowOperator
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileComputeMode, \
    CompileParallelism, CompileLanguage
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.runtime.debugger.history.historyState import HistoryState
from spe.common.tuple import Tuple


class TumblingWindowTime(WindowOperator):
    def __init__(self, opID: int):
        super(TumblingWindowTime, self).__init__(opID, 1, 1, supportsDebugging=False)

        self.value = 0

        self.buffer: List[Tuple] = list()
        self.timer: Optional[Timer] = None

    def setData(self, data: json):
        self.value = float(data["value"])

        # If pipeline is running, modify timer
        if self.isRunning():
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None

            if self.value > 0:
                self.timer = Timer(self.value, self._distributeBuffer)  # This breaks the debugging, not possible in this case
                self.timer.start()

    def getData(self) -> dict:
        return {"value": self.value}

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super(TumblingWindowTime, self).onRuntimeCreate(eventLoop)

        if self.value > 0:
            self.timer = Timer(self.value, self._distributeBuffer)
            self.timer.start()

    def _distributeBuffer(self):
        # When the pipeline is paused this timer shouldn't trigger!
        if self.isDebuggingEnabled() and self.getHistoryState() != HistoryState.INACTIVE:
            return

        hasConnections = False
        for o in self.outputs:
            if o.hasConnections():
                hasConnections = True
                break

        # In case op was disconnected or pipeline stopped
        if not self.isRunning() or not hasConnections:
            return

        if len(self.buffer) > 0:
            r = Window(self.buffer.copy())
            self.buffer.clear()

            tup = self.createTuple((r,))  # If debugging should be supported we need to create a DT manually for the res tuple

            asyncio.ensure_future(self._onTupleProcessed(tup, self.value), loop=self._eventLoop)

        self.timer = Timer(self.value, self._distributeBuffer)
        self.timer.start()

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self.buffer.append(tupleIn)

        return None  # Distribution will be handled by timer

    # -------------------------- Compilation -------------------------

    def deriveOutThroughput(self, inTp: float):
        return 1 / self.value

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        # window_all for non-keyed streams, window else
        def getPyFlinkCode(compileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.window import TumblingEventTimeWindows
            from pyflink.common.time import Time""",
                PyFlinkCodeTemplate.Section.ASSIGNMENTS: f"""
            $inDS.window_all(TumblingEventTimeWindows.of(Time.seconds({self.value})))"""})  # Currently only for non-keyed streams

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.WINDOW, getPyFlinkCode))]
