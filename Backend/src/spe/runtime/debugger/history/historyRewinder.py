import threading
from typing import Optional

from config import DEBUGGER_HISTORY_REWIND_BASE_STEP_FREQUENCY
from utils.preciseEvent import PreciseEvent


# TODO: FIX !!!


class HistoryRewinder:
    def __init__(self, debugger):
        from spe.runtime.debugger.pipelineDebugger import PipelineDebugger
        self._debugger: PipelineDebugger = debugger

        self._enabled = False
        self._forward = True
        self._rewindThread: Optional[threading.Thread] = None
        self._rewindWaitEvent: Optional[PreciseEvent] = None
        self._rewindSpeed = 1.0
        self._useStepTime = True

    def updateStatus(self, enabled: bool, forward: bool) -> bool:
        self._forward = forward

        if enabled and self.isRunning():
            return True  # Already running, no need to change status

        self._enabled = enabled

        # Stop rewind
        if self._rewindThread is not None and not self.isRunning():
            self._stop()

        return False

    def setSpeed(self, rewindSpeed: float, useStepTime: bool):
        # Interrupt wait in case speed has changed
        if self._rewindThread is not None and self._rewindSpeed != rewindSpeed:
            self._rewindWaitEvent.set()

        self._useStepTime = useStepTime
        self._rewindSpeed = rewindSpeed

    def startMaybe(self) -> bool:
        if not self.isRunning():
            return False

        if self._rewindThread is not None:
            return True  # Already started

        self._rewindWaitEvent = PreciseEvent()
        self._rewindThread = threading.Thread(target=self._executeRewind)
        self._rewindThread.start()

        return True

    def reset(self):
        self._enabled = False

        # release lock and wait until thread stopped completely
        if self._rewindThread is not None:
            self._rewindWaitEvent.set()

            with self._debugger.getHistoryLock():
                ...  # Waiting ..

        self._rewindThread = None
        self._rewindWaitEvent = None

        self._rewindSpeed = 1.0

        # if self._debugger.isEnabled():
        #    self._debugger.sendStepData() TODO: DONT SEND DATA IF DEBUGGER IS DISABLED

    def _stop(self):
        if self._rewindThread is not None:
            self._rewindWaitEvent.set()

        self._enabled = False

        # Update data if it was running
        self._debugger.sendStepData()

    def _executeRewind(self):
        # First locks history until rewind is done or canceled
        # Second sets system clock to 1ms if on Windows (will be reset after) - required for accurate wait event
        with self._debugger.getHistoryLock():
            lastTime = self._debugger.getLastGlobalStep().time

            def executeStep(stepID):
                nonlocal lastTime

                step = self._debugger.getGlobalStep(stepID)
                speedFac = (1 / self._rewindSpeed) if self._rewindSpeed != 0 else 1

                if self._useStepTime:
                    sleepTime = abs(step.time - lastTime) * speedFac
                else:
                    sleepTime = (1 / DEBUGGER_HISTORY_REWIND_BASE_STEP_FREQUENCY) * speedFac

                if sleepTime > 0:
                    self._rewindWaitEvent.wait(sleepTime)

                    if not self.isRunning():
                        return

                    self._rewindWaitEvent.clear()  # May have been reset at this point

                lastTime = step.time

                self._debugger.setHistoryStep(stepID)
                self._debugger.sendStepData()

            while self.isRunning():
                nextStep = self._debugger.getCurrentStepID() + (1 if self._forward else -1)

                if nextStep < 0 or nextStep >= self._debugger.getGlobalStepCount():
                    break  # Reach end of steps

                if not self.isRunning():
                    break

                executeStep(nextStep)

            self._rewindThread = None
            self._rewindWaitEvent = None

            self._stop()

    def getStatus(self) -> Optional[int]:
        if not self.isRunning():
            return None
        return 1 if self._forward else 2

    def isRunning(self) -> bool:
        return self._enabled
