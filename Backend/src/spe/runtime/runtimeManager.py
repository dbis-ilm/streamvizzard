import asyncio
import gc
import logging
import threading
import traceback
from contextlib import nullcontext
from enum import Enum
from threading import Thread
from typing import Optional, List

import config
from spe.pipeline.pipeline import Pipeline
from spe.pipeline.pipelineUpdates import PipelineUpdate
from spe.runtime.runtimeCommunicator import RuntimeCommunicator
from spe.runtime.structures.timer import Timer
from utils.utils import isWindowsOS

if isWindowsOS():
    import wres


class RuntimeState(Enum):
    RUNNING = 1
    STOPPING = 2
    STARTING = 3
    NONE = 4


class RuntimeManager:
    def __init__(self, serverManager):
        self._pipeline: Optional[Pipeline] = None

        self.thread: Optional[Thread] = None
        self.asyncioLoop: Optional[asyncio.AbstractEventLoop] = None

        self.shutdownEvent: Optional[threading.Event] = None

        self.state = RuntimeState.NONE

        self._serverManager = serverManager

        self._runtimeCommunicator = RuntimeCommunicator(self._serverManager, self)

    def _startApp(self):
        print("\nStarting Pipeline...")

        logging.basicConfig(level=logging.INFO)

        self._pipeline.createRuntime(self.asyncioLoop)

        self.state = RuntimeState.RUNNING

    def _runtimeThreadFunc(self):
        self.asyncioLoop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.asyncioLoop)

        self._startApp()

        self._runtimeCommunicator.onPipelineStarted()

        try:
            # Second sets system clock to max res if on Windows (will be reset after) - required for accurate time events 10000
            with wres.set_resolution(0) if isWindowsOS() else nullcontext():
                self.asyncioLoop.run_forever()
        except Exception as e:
            print(e)
        finally:
            self._shutdownApp()

    def startPipeline(self, pipeline: Pipeline):
        if self.state is not RuntimeState.NONE:
            return

        if config.MISC_PRINT_PIPELINE_ON_START:
            pipeline.describe()

        self.shutdownEvent = threading.Event()

        self.state = RuntimeState.STARTING

        Timer.reset()

        self._pipeline = pipeline

        self.thread = threading.Thread(target=self._runtimeThreadFunc, daemon=True)
        self.thread.start()

        self._runtimeCommunicator.onPipelineStarting()

    async def _stopEventLoop(self):
        self.asyncioLoop.stop()

    def _shutdownApp(self):
        self.asyncioLoop.close()

        self.asyncioLoop = None

        self.thread = None

        self.state = RuntimeState.NONE

        self._runtimeCommunicator.onPipelineStopped()

        self._pipeline = None

        gc.collect()

        self.shutdownEvent.set()

        print("Pipeline shutdown")

    async def _updatePipelineInternal(self, updates: List[PipelineUpdate]):
        try:
            for update in updates:
                self._pipeline.executeEvent(Pipeline.EVENT_PIPELINE_PRE_UPDATED, [update])

                update.updatePipeline(self._pipeline)

                self._pipeline.executeEvent(Pipeline.EVENT_PIPELINE_UPDATED, [update])
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

    def updatePipeline(self, updates: List[PipelineUpdate]):
        if not self.isRunning():
            return

        asyncio.run_coroutine_threadsafe(self._updatePipelineInternal(updates), loop=self.asyncioLoop)

    def changeHeatmap(self, hmType):
        self._runtimeCommunicator.changeHeatmap(hmType)

    def changeDebuggerStep(self, targetStep: int, targetBranch: int):
        if not self.isRunning():
            return

        self._runtimeCommunicator.changeDebuggerStep(targetStep, targetBranch)

    def requestDebuggerStep(self, targetBranch: int, targetTime: float):
        if not self.isRunning():
            return

        self._runtimeCommunicator.requestDebuggerStep(targetBranch, targetTime)

    def changeDebuggerState(self, historyActive: bool, historyRwd: Optional[int]):
        if not self.isRunning():
            return

        self._runtimeCommunicator.changeDebuggerState(historyActive, historyRwd)

    def changeDebuggerConfig(self, enabled: bool, memoryLimit: Optional[int], storageLimit: Optional[int],
                             historyRewindSpeed: float, historyRwdUseStepTime: bool):
        self._runtimeCommunicator.changeDebuggerConfig(enabled, memoryLimit, storageLimit, historyRewindSpeed, historyRwdUseStepTime)

    def toggleAdvisor(self, enabled: bool):
        self._runtimeCommunicator.toggleAdvisor(enabled)

    def _stopPipeline(self):
        if self.state is RuntimeState.NONE \
                or self.state is RuntimeState.STOPPING:
            return

        self.state = RuntimeState.STOPPING

        self._runtimeCommunicator.onPipelineStopping()

        self._pipeline.shutdown()

        # Gracefully shutdown event loop

        for task in asyncio.all_tasks(self.asyncioLoop):
            task.cancel()

        asyncio.run_coroutine_threadsafe(self._stopEventLoop(), loop=self.asyncioLoop)

    def shutdown(self):
        self._stopPipeline()

        self.shutdownEvent.wait()

    def isRunning(self) -> bool:
        return self.state == RuntimeState.RUNNING

    def getPipeline(self) -> Pipeline:
        return self._pipeline

    def getEventLoop(self) -> asyncio.AbstractEventLoop:
        return self.asyncioLoop
