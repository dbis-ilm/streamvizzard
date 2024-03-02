import json
import os
import time

from spe.pipeline.operators.source import Source


class ReadFolder(Source):
    def __init__(self,  opID: int):
        super(ReadFolder, self).__init__(opID, 0, 1)

        self.path = ""
        self.repeat = False
        self.rate = 0

    def setData(self, data: json):
        self.path = data["path"]

        self.repeat = data["repeat"] == 1

        self.rate = data["rate"]

    def getData(self) -> dict:
        return {"path": self.path, "repeat": 1 if self.repeat else 0, "rate": self.rate}

    def _runSource(self):
        init = False

        while self.isRunning():
            if init and not self.repeat:  # To allow dynamic enable / disable of repeat
                time.sleep(0.25)

                continue

            init = True
            currentPath = self.path

            try:
                files = os.listdir(self.path)

                for f in files:
                    if not self.isRunning() or currentPath != self.path:
                        break

                    self._produce((os.path.join(self.path, f),))

                    if 0 < self.rate < 100:
                        time.sleep(1 / self.rate)
            except Exception:
                self.onExecutionError()
