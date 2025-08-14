import asyncio
import time
from asyncio import AbstractEventLoop
from typing import Optional

from spe.common.timer import Timer


class SimulationTick:
    def __init__(self, duration: float):
        self._tickRate = 1.0 / 1000  # 1ms
        self._endTime = Timer.currentTime() + duration

        self._loop: Optional[AbstractEventLoop] = None

        self._waitingOps = 0

    def start(self, eventLoop: AbstractEventLoop):
        self._loop = eventLoop

        # asyncio.run_coroutine_threadsafe(self._run(), loop=self._loop)

    def isCompleted(self):
        return Timer.currentTime() >= self._endTime

    def waitDuration(self, duration: float):
        self._waitingOps += 1
        endTime = Timer.currentTime() + duration

        while Timer.currentTime() < endTime:
            time.sleep(self._tickRate)  # Min Sleep required otherwise we freeze GIL

        self._waitingOps -= 1

    async def _run(self):
        while not self.isCompleted():
            while self._waitingOps > 0:
                # This is too fast, we lose tuples, sources should progress the time?
                # Calc how many tuples each sources produces in the duration and send them through pipeline
                # How to track time with multiple sources? ... global tick required...
                # "Event based Simulation"
                await asyncio.sleep(self._tickRate, loop=self._loop)

                # Timer.offsetTime(self._tickRate * 2)

            await asyncio.sleep(self._tickRate, loop=self._loop)
