import json
import random
import string
import time

from spe.pipeline.operators.source import Source


class RandomData(Source):
    def __init__(self,  opID: int):
        super(RandomData, self).__init__(opID, 0, 1)

        self.rate = 0
        self.limitRate = True

    def setData(self, data: json):
        self.rate = data["rate"]
        self.limitRate = data["limitRate"]

    def getData(self) -> dict:
        return {"rate": self.rate, "limitRate": self.limitRate}

    def _runSource(self):
        while self.isRunning():
            data = {
                "val1": random.random(),
                "val2": random.randint(1, 100),
                "val3": "".join(random.choices(string.ascii_letters, k=10)),
                "val4": [random.random() for _ in range(10)]
            }

            self._produce((data,))

            if self.limitRate:
                sleepDuration = 1 / self.rate

                if sleepDuration > 1e-3:
                    time.sleep(1 / self.rate)
