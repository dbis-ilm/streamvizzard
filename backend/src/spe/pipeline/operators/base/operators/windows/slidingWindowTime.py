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
class SlidingWindowTime(WindowOperator):
    def __init__(self, opID: int):
        super(SlidingWindowTime, self).__init__(opID, 1, 1, supportsDebugging=False)

        self.interval = 0
        self.slide = 0

        self._buffer: List[Tuple] = list()

        self._event: Optional[TimerHandle] = None

    def setData(self, data: Dict):
        self.interval = float(data["interval"])
        self.slide = min(self.interval, float(data["slide"]))

        # If pipeline is running, reschedule
        if self.isRunning():
            self._scheduleWindow()

    def getData(self) -> dict:
        return {"interval": self.interval, "slide": self.slide}

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super(SlidingWindowTime, self).onRuntimeCreate(eventLoop)

        self._scheduleWindow()

    def _scheduleWindow(self):
        # Cancel previous

        if self._event is not None:
            self._event.cancel()
            self._event = None

        self._event = self.getEventLoop().call_later(self.slide, lambda: asyncio.ensure_future(self._triggerWindow(), loop=self.getEventLoop()))

    async def _triggerWindow(self):
        self._event = None

        if not self.isRunning():
            return

        # When the pipeline is paused this timer shouldn't trigger! If we want support debugging, we must schedule window when debugging stops (but consider already elapsed time!)
        if self.isDebuggingEnabled() and self.getHistoryState() != HistoryState.INACTIVE:
            return

        start = Timer.currentTime()

        # Lightweight operation, so we execute it on the event loop thread

        if len(self._buffer) > 0 and start - self._buffer[0].eventTime >= self.interval:
            # Emit all currently stored tuples. [Low-effort implementation]
            # Due to timing variations, this might also include tuples slightly outside the defined window interval.
            # But we can't drop them since this would risk to lose tuples if they have not appeared in a window before.

            emittedWindow = Window(self._buffer.copy())

            # Remove outdated values outside the interval from buffer

            removeFromIdx = 0

            for tupIdx in range(len(self._buffer)):
                tup = self._buffer[tupIdx]

                if start - tup.eventTime <= self.interval:  # First valid entry within interval
                    removeFromIdx = tupIdx - 1

                    break

            self._buffer = self._buffer[removeFromIdx + 1:]

            exDur = Timer.currentTime() - start  # Actual processing time instead of "waitingTime" of window

            # If debugging should be supported we need to create a DT manually for the res tuple
            await self._onTupleProcessed(self.createTuple((emittedWindow,)), exDur)

        self._scheduleWindow()

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self._buffer.append(tupleIn)

        return None  # Distribution will be handled by timer

    # -------------------------- Compilation -------------------------

    def deriveOutThroughput(self, inTp: float):
        return 1 / self.slide

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(cfg: OpCompileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            # Despite the availability of SlidingEventTimeWindows, processing time more accurately reflects the SV logic
            # Moreover, currently, EventTime can not be leveraged by the user!

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.window import SlidingProcessingTimeWindows
            from pyflink.common.time import Time""",
                PyFlinkCodeTemplate.Section.ASSIGNMENTS:
                    self._getPyFlinkCompileAssignment(f"SlidingProcessingTimeWindows.of(Time.milliseconds({int(self.interval * 1000)}), Time.milliseconds({int(self.slide * 1000)}))", cfg.parallelismCount)})

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.WINDOW, getPyFlinkCode))]
