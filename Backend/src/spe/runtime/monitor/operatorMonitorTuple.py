import math

from spe.runtime.structures.timer import Timer


class OperatorMonitorTuple:
    def __init__(self, executionDuration: float, outputSize: int):
        self.timeStamp = Timer.currentTime()
        self.executionDuration = executionDuration  # In ms
        self.outputSize = outputSize  # In bytes

    def __eq__(self, other):
        return (math.isclose(self.timeStamp, other.timeStamp)
                and math.isclose(self.executionDuration, other.executionDuration)
                and self.outputSize == other.outputSize)

    def toJSON(self):
        return {"timeStamp": self.timeStamp,
                "exDuration": self.executionDuration,
                "outputSize": self.outputSize}
