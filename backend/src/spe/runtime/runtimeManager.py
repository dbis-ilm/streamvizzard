from __future__ import annotations
import asyncio
import gc
import logging
import threading
import traceback
from contextlib import nullcontext
from enum import Enum
from threading import Thread
from typing import Optional, List, Callable, TYPE_CHECKING

from spe.pipeline.pipeline import Pipeline
from spe.pipeline.pipelineUpdates import PipelineUpdate
from spe.runtime.runtimeGateway import RuntimeGateway
from spe.common.timer import Timer
from streamVizzard import StreamVizzard
from utils.svResult import SvResult
from utils.utils import isWindowsOS

if TYPE_CHECKING:
    from network.server import ServerManager

if isWindowsOS():
    import wres


class RuntimeState(Enum):
    RUNNING = 1
    STOPPING = 2
    STARTING = 3
    NONE = 4


class RuntimeManager:
    def __init__(self, serverManager: ServerManager):
        self._pipeline: Optional[Pipeline] = None

        self.thread: Optional[Thread] = None
        self.asyncioLoop: Optional[asyncio.AbstractEventLoop] = None

        self._startupEvent: Optional[threading.Event] = None
        self._shutdownEvent: Optional[threading.Event] = None

        self.state = RuntimeState.NONE

        self._serverManager = serverManager

        self._gateway = RuntimeGateway(self._serverManager, self)

    def startPipeline(self, pipeline: Pipeline, preStartCallback: Optional[Callable] = None) -> SvResult:
        if self.state is not RuntimeState.NONE:
            return SvResult.error("Pipeline already running!")

        if StreamVizzard.getConfig().MISC_PRINT_PIPELINE_ON_START:
            pipeline.describe()

        self._startupEvent = threading.Event()
        self._shutdownEvent = threading.Event()

        self.state = RuntimeState.STARTING

        Timer.reset()

        self._pipeline = pipeline
        self.asyncioLoop = asyncio.new_event_loop()

        self._gateway.onPipelineStarting()

        if preStartCallback is not None:
            preStartCallback()

        self.thread = threading.Thread(target=self._pipelineRuntimeThread, daemon=True)
        self.thread.start()

        self._startupEvent.wait()  # Wait until pipeline is started

        return SvResult.ok() if self.isRunning() else SvResult.error("Pipeline failed to start!")

    def _pipelineRuntimeThread(self):
        asyncio.set_event_loop(self.asyncioLoop)

        print("\nStarting Pipeline...")

        if self._pipeline.createRuntime(self.asyncioLoop):
            self.state = RuntimeState.RUNNING

            self._gateway.onPipelineStarted()
        else:
            self._serverManager.flushSocketData()  # Flush errors before resetting

            self._stopPipeline()

        self._startupEvent.set()

        try:
            # Run loop until cancellation

            if self.isRunning():

                # Second sets system clock to max res if on Windows (will be reset after) - required for accurate time events 10000
                with wres.set_resolution(0) if isWindowsOS() else nullcontext():
                    self.asyncioLoop.run_forever()

            # Run loop until all shutdown clean up is done

            else:
                tasks = [t for t in asyncio.all_tasks(self.asyncioLoop)]
                self.asyncioLoop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())
        finally:
            self._shutdownPipelineRuntime()

    def _shutdownPipelineRuntime(self):
        self.asyncioLoop.close()

        self.asyncioLoop = None

        self.thread = None

        self.state = RuntimeState.NONE

        self._gateway.onPipelineStopped()

        self._pipeline = None

        gc.collect()

        self._shutdownEvent.set()

        print("Pipeline shutdown")

    def updatePipeline(self, updates: List[PipelineUpdate]):
        if not self.isRunning():
            return

        asyncio.run_coroutine_threadsafe(self._updatePipelineInternal(updates), loop=self.asyncioLoop)

    async def _updatePipelineInternal(self, updates: List[PipelineUpdate]):
        try:
            for update in updates:
                self._pipeline.executeEvent(Pipeline.EVENT_PIPELINE_PRE_UPDATED, [update])

                update.updatePipeline(self._pipeline)

                self._pipeline.executeEvent(Pipeline.EVENT_PIPELINE_UPDATED, [update])
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

    def stopPipeline(self):
        self._stopPipeline()

        if self._shutdownEvent is not None:  # There might be no pipeline running
            self._shutdownEvent.wait()

    def _stopPipeline(self):
        if self.state is RuntimeState.NONE \
                or self.state is RuntimeState.STOPPING:
            return

        self.state = RuntimeState.STOPPING

        self._gateway.onPipelineStopping()

        self._pipeline.shutdown()

        # Gracefully schedule all tasks for shutdown and close loop

        for task in asyncio.all_tasks(self.asyncioLoop):
            task.cancel()

        asyncio.run_coroutine_threadsafe(self._stopEventLoop(), loop=self.asyncioLoop)

    async def _stopEventLoop(self):
        self.asyncioLoop.stop()

    def shutdown(self):
        self.stopPipeline()  # Waits until the pipeline is stopped

        self._gateway.onRuntimeShutdown()

    def isRunning(self) -> bool:
        return self.state == RuntimeState.RUNNING

    def getPipeline(self) -> Pipeline:
        return self._pipeline

    def getEventLoop(self) -> asyncio.AbstractEventLoop:
        return self.asyncioLoop

    @property
    def gateway(self) -> RuntimeGateway:
        return self._gateway
