import asyncio
import json
import threading
from typing import Optional, List

from spe.common.timer import Timer
from spe.pipeline.operators.base.dataTypes.window import Window
from spe.pipeline.operators.base.operators.windows.windowOperator import WindowOperator
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileComputeMode, \
    CompileParallelism, CompileLanguage
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from spe.runtime.debugger.history.historyState import HistoryState
from spe.common.tuple import Tuple


class TumblingWindowTime(WindowOperator):
    def __init__(self, opID: int):
        super(TumblingWindowTime, self).__init__(opID, 1, 1, supportsDebugging=False)

        self.value = 0

        self.buffer: List[Tuple] = list()
        self.timer: Optional[threading.Timer] = None

    def setData(self, data: json):
        self.value = float(data["value"])

        # If pipeline is running, modify timer
        if self.isRunning():
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None

            if self.value > 0:
                self.timer = threading.Timer(self.value, self._distributeBuffer)  # This breaks the debugging, not possible in this case
                self.timer.start()

    def getData(self) -> dict:
        return {"value": self.value}

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super(TumblingWindowTime, self).onRuntimeCreate(eventLoop)

        if self.value > 0:
            self.timer = threading.Timer(self.value, self._distributeBuffer)
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
            start = Timer.currentRealTime()

            r = Window(self.buffer.copy())
            self.buffer.clear()

            tup = self.createTuple((r,))  # If debugging should be supported we need to create a DT manually for the res tuple

            exDur = Timer.currentRealTime() - start  # Actual processing time instead of "waitingTime" of window

            asyncio.ensure_future(self._onTupleProcessed(tup, exDur), loop=self._eventLoop)

        self.timer = threading.Timer(self.value, self._distributeBuffer)
        self.timer.start()

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self.buffer.append(tupleIn)

        return None  # Distribution will be handled by timer

    # -------------------------- Compilation -------------------------

    def deriveOutThroughput(self, inTp: float):
        return 1 / self.value

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(cfg: OpCompileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            # Despite the availability of TumblingEventTimeWindows, processing time more accurately reflects the SV logic
            # Moreover, currently, EventTime can not be leveraged by the user!

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.window import TumblingProcessingTimeWindows
            from pyflink.common.time import Time""",
                PyFlinkCodeTemplate.Section.ASSIGNMENTS:
                    self._getPyFlinkCompileAssignment(f"TumblingProcessingTimeWindows.of(Time.milliseconds({int(self.value * 1000)}))", cfg.parallelismCount)})

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.WINDOW, getPyFlinkCode))]
