import json
import time

from spe.pipeline.operators.source import Source


class TextFile(Source):
    def __init__(self,  opID: int):
        super(TextFile, self).__init__(opID, 0, 1)

        self.path = ""
        self.lineSep = ""
        self.repeat = False
        self.rate = 0

    def setData(self, data: json):
        self.path = data["path"]
        self.lineSep = data["lineSep"]

        self.repeat = data["repeat"] == 1

        self.rate = data["rate"]

    def getData(self) -> dict:
        return {"path": self.path, "lineSep": self.lineSep, "repeat": 1 if self.repeat else 0, "rate": self.rate}

    def _runSource(self):
        init = False

        while self.isRunning():
            if init and not self.repeat:  # To allow dynamic enable / disable of repeat
                time.sleep(0.25)

                continue

            init = True

            try:
                with open(self.path) as file:
                    currentPath = self.path

                    while line := file.readline():
                        if not self.isRunning() \
                                or currentPath != self.path:
                            break

                        line = line.strip()

                        self._produce((line,))

                        if 0 < self.rate < 100:
                            time.sleep(1 / self.rate)
            except Exception:
                self.onExecutionError()
