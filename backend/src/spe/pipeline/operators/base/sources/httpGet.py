import json
import time

import requests

from spe.pipeline.operators.source import Source


class HTTPGet(Source):
    def __init__(self,  opID: int):
        super(HTTPGet, self).__init__(opID, 0, 1)

        self.url = ""
        self.rate = 0

    def setData(self, data: json):
        self.url = data["url"]
        self.rate = data["rate"]

    def getData(self) -> dict:
        return {"url": self.url, "rate": self.rate}

    def _runSource(self):
        while self.isRunning():
            try:
                r = requests.get(self.url)

                self._produce((r.text,))

                if 0 < self.rate < 100:
                    time.sleep(1 / self.rate)
            except Exception:
                self.onExecutionError()
