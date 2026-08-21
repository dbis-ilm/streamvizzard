import asyncio
from asyncio import TimerHandle
from typing import Optional, List, Dict

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


# TODO: Check if we can support debugging
class TumblingWindowTime(WindowOperator):
    def __init__(self, opID: int):
        super(TumblingWindowTime, self).__init__(opID, 1, 1, supportsDebugging=False)

        self.value = 0

        self._buffer: List[Tuple] = list()

        self._event: Optional[TimerHandle] = None

    def setData(self, data: Dict):
        self.value = float(data["value"])

        # If pipeline is running, reschedule
        if self.isRunning():
            self._scheduleWindow()

    def getData(self) -> dict:
        return {"value": self.value}

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super(TumblingWindowTime, self).onRuntimeCreate(eventLoop)

        self._scheduleWindow()

    def _scheduleWindow(self):
        # Cancel previous

        if self._event is not None:
            self._event.cancel()
            self._event = None

        self._event = self.getEventLoop().call_later(self.value, lambda: asyncio.ensure_future(self._triggerWindow(), loop=self.getEventLoop()))

    async def _triggerWindow(self):
        self._event = None

        if not self.isRunning():
            return

        # When the pipeline is paused this timer shouldn't trigger! If we want support debugging, we must schedule window when debugging stops
        if self.isDebuggingEnabled() and self.getHistoryState() != HistoryState.INACTIVE:
            return

        # Extremely lightweight operation, so we execute it on the event loop thread
        if len(self._buffer) > 0:
            start = Timer.currentRealTime()

            r = Window(self._buffer)
            self._buffer = []

            exDur = Timer.currentRealTime() - start  # Actual processing time instead of "waitingTime" of window

            # If debugging should be supported we need to create a DT manually for the res tuple

            await self._onTupleProcessed(self.createTuple((r,)), exDur)

        self._scheduleWindow()

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self._buffer.append(tupleIn)

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
