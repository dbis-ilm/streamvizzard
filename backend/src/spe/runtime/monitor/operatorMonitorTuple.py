import math


class OperatorMonitorTuple:
    def __init__(self, executionDuration: float, outputSize: int):
        self.executionDuration = executionDuration  # In ms
        self.outputSize = outputSize  # In bytes

        self.prevAvgExecutionDuration = 0  # Calculated
        self.prevAvgDataSize = 0  # Calculated

    def __eq__(self, other):
        return (math.isclose(self.executionDuration, other.executionDuration)
                and math.isclose(self.prevAvgExecutionDuration, other.prevAvgExecutionDuration)
                and math.isclose(self.prevAvgDataSize, other.prevAvgDataSize)
                and self.outputSize == other.outputSize)

    def __hash__(self):
        return id(self)

    def toJSON(self):
        return {"exDuration": self.executionDuration,
                "outputSize": self.outputSize,
                "prevAvgExecutionDuration": self.prevAvgExecutionDuration,
                "prevAvgDataSize": self.prevAvgDataSize}
