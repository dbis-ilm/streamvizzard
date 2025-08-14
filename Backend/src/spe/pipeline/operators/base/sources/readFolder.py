import json
import os
import time
from pathlib import Path

from spe.pipeline.operators.source import Source


class ReadFolder(Source):
    def __init__(self,  opID: int):
        super(ReadFolder, self).__init__(opID, 0, 1)

        self.path = ""
        self.repeat = False
        self.rate = 0
        self.limitRate = 0

    def setData(self, data: json):
        self.path = data["path"]
        self.limitRate = data["limitRate"]
        self.repeat = data["repeat"]
        self.rate = data["rate"]

    def getData(self) -> dict:
        return {"path": self.path, "repeat": self.repeat, "rate": self.rate, "limitRate": self.limitRate}

    def _runSource(self):
        init = False

        while self.isRunning():
            if init and not self.repeat:  # To allow dynamic enable / disable of repeat
                time.sleep(0.25)

                continue

            init = True
            currentPath = self.path

            try:
                files = sorted(Path(self.path).iterdir())  # Sorted my name

                for f in files:
                    if not self.isRunning() or currentPath != self.path:
                        break

                    self._produce((os.path.join(self.path, f),))

                    if self.limitRate:
                        sleepDuration = 1 / self.rate

                        if sleepDuration > 1e-3:
                            time.sleep(1 / self.rate)
            except Exception:
                self.onExecutionError()
