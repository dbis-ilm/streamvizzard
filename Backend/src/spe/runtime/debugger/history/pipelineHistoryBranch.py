from __future__ import annotations

from collections import deque
from typing import Deque, Optional, Dict, List

from spe.runtime.debugger.debugStep import DebugStep


class PipelineHistoryStepRemoveResult:
    def __init__(self, removedStep: DebugStep):
        self.removedStep = removedStep
        self.removedParentBranch: Optional[PipelineHistoryBranch] = None
        self.removedChildBranches: Optional[List[PipelineHistoryBranch]] = None


class PipelineHistoryBranch:
    def __init__(self, branchID: int, parentBranch: Optional[PipelineHistoryBranch] = None):
        self.id = branchID

        self._steps: Deque[DebugStep] = deque()

        self.stepIDOffset = 0  # If we start removing steps we adjust this offset to still access the steps inside the deque

        self.parentBranch = parentBranch
        self.childBranches: Dict[int, List[PipelineHistoryBranch]] = dict()  # idx of root step in steps list, branches

    def registerStep(self, step: DebugStep) -> int:
        self._steps.append(step)

        step.localID = self.getStepCount() - 1 + self.stepIDOffset
        step.branchID = self.id

        return step.localID

    def removeFirstStep(self) -> Optional[PipelineHistoryStepRemoveResult]:
        if self.getStepCount() == 0:
            return None

        # Remove actual first step

        removed = self._steps.popleft()

        self.stepIDOffset += 1

        removeRes = PipelineHistoryStepRemoveResult(removed)

        # Remove parent branch if it's the first step (stepID=0), also remove child entry in parent for us

        if removed.localID == 0 and self.parentBranch is not None:
            removeRes.removedParentBranch = self.parentBranch

            splitID = self.parentBranch.getSplitStepIDForChild(self)
            childrenOfParent = self.parentBranch.childBranches[splitID]

            childrenOfParent.remove(self)

            if len(childrenOfParent) == 0:
                del self.parentBranch.childBranches[splitID]

            self.parentBranch = None

        # Remove children that were connected with this removed step, also remove parent entry of child

        children = self.childBranches.get(removed.localID, None)

        if children is not None:
            removeRes.removedChildBranches = children

            del self.childBranches[removed.localID]

            for child in children:
                child.parentBranch = None

        return removeRes

    def clearSteps(self):
        self._steps.clear()

    def findRootBranch(self) -> Optional[PipelineHistoryBranch]:
        currentParent = self.parentBranch

        if currentParent is None:
            return self

        while currentParent.parentBranch is not None:
            currentParent = currentParent.parentBranch

        return currentParent

    def getStep(self, stepID: int):
        idx = stepID - self.stepIDOffset

        return self._steps[idx] if idx >= 0 else None

    def getAllSteps(self):
        return self._steps

    def getLastStep(self) -> Optional[DebugStep]:
        ln = self.getStepCount()

        return self._steps[ln - 1] if ln > 0 else None

    def getFirstStep(self) -> Optional[DebugStep]:
        ln = self.getStepCount()

        return self._steps[0] if ln > 0 else None

    def getStepCount(self) -> int:
        return len(self._steps)

    def addChild(self, branch: PipelineHistoryBranch, splitStep: int):
        cs = self.childBranches.get(splitStep, [])
        cs.append(branch)
        self.childBranches[splitStep] = cs

    def getSplitStepIDForChild(self, childBranch: PipelineHistoryBranch) -> Optional[int]:
        for [stepID, brs] in self.childBranches.items():
            for br in brs:
                if childBranch == br:
                    return stepID

        return None
