from __future__ import annotations

import json
import threading
from typing import TYPE_CHECKING, Optional

from streamVizzard import StreamVizzard
from spe.common.preciseEvent import PreciseEvent

if TYPE_CHECKING:
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger


class HistoryRewinder:
    def __init__(self, debugger: PipelineDebugger):
        self._debugger = debugger

        self._enabled = False
        self._forward = True
        self._rewindThread: Optional[threading.Thread] = None
        self._rewindWaitEvent: Optional[PreciseEvent] = None
        self._rewindSpeed = 1.0
        self._useStepTime = True

    def setSpeed(self, rewindSpeed: float, useStepTime: bool):
        # Interrupt wait in case speed has changed
        if self._rewindThread is not None and self._rewindSpeed != rewindSpeed:
            self._rewindWaitEvent.set()

        self._useStepTime = useStepTime
        self._rewindSpeed = rewindSpeed

    def start(self, forward: bool):
        if self.isRunning():
            return

        self._enabled = True
        self._forward = forward

        self._rewindWaitEvent = PreciseEvent()
        self._rewindThread = threading.Thread(target=self._executeRewind)
        self._rewindThread.start()

        self._debugger.getServerManager().sendSocketData(json.dumps({"cmd": "debRewind", "status": self.getStatus()}))

    def reset(self):
        if not self.isRunning():
            return

        self._enabled = False

        # release lock and wait until thread stopped completely
        if self._rewindThread is not None:
            self._rewindWaitEvent.set()

            with self._debugger.getHistoryLock():
                ...  # Waiting ..

        self._rewindThread = None
        self._rewindWaitEvent = None

        if self._debugger.isEnabled():
            self._debugger.getServerManager().sendSocketData(json.dumps({"cmd": "debRewind", "status": self.getStatus()}))

    def _executeRewind(self):
        # First locks history until rewind is done or canceled

        BASE_STEP_FREQ = StreamVizzard.getConfig().DEBUGGER_HISTORY_REWIND_BASE_STEP_FREQUENCY

        with self._debugger.getHistoryLock():
            lastTime = self._debugger.getHistory().getCurrentStep().time
            currentBranch = self._debugger.getHistory().getCurrentBranch()

            def executeStep(stepID):
                nonlocal lastTime

                step = currentBranch.getStep(stepID)
                speedFac = (1 / self._rewindSpeed) if self._rewindSpeed != 0 else 1

                if self._useStepTime:
                    sleepTime = abs(step.time - lastTime) * speedFac
                else:
                    sleepTime = (1 / BASE_STEP_FREQ) * speedFac

                if sleepTime > 0.001:
                    self._rewindWaitEvent.wait(sleepTime)

                    if not self.isRunning():
                        return

                    self._rewindWaitEvent.clear()  # May have been reset at this point

                lastTime = step.time

                self._debugger.setHistoryStep(stepID, currentBranch.id)

            while self.isRunning():
                nextStep = self._debugger.getHistory().getCurrentStepID() + (1 if self._forward else -1)

                if nextStep < currentBranch.getFirstStep().localID or nextStep >= currentBranch.getLastStep().localID:
                    break  # Reach end of steps

                if not self.isRunning():
                    break

                executeStep(nextStep)

            self.reset()

    def getStatus(self) -> Optional[int]:
        if not self.isRunning():
            return None
        return 1 if self._forward else 2

    def isRunning(self) -> bool:
        return self._enabled
