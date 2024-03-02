from spe.runtime.debugger.debugStep import DebugStepType


class DebugBreakpoint:
    def __init__(self, enabled: bool, stepType: DebugStepType, amount: int):
        self.enabled = enabled
        self.stepType = stepType
        self.amount = amount

    def isTriggered(self, executedStep: DebugStepType, amount: int) -> bool:
        return self.enabled and self.stepType == executedStep and amount >= self.amount
