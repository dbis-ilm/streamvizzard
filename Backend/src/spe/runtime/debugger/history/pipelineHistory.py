from __future__ import annotations

import json
from collections import deque
from typing import TYPE_CHECKING, Optional, Dict, List, Set, Deque, Callable

from spe.runtime.debugger.debugStep import DebugStep, DebugStepType
from spe.runtime.debugger.history.historyState import HistoryState
from spe.runtime.debugger.history.pipelineHistoryBranch import PipelineHistoryBranch
from spe.runtime.runtimeCommunicator import getRuntimeManager
from utils.utils import clamp, printWarning

if TYPE_CHECKING:
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger


class PipelineHistory:
    def __init__(self, debugger: PipelineDebugger):
        self._debugger = debugger
        self._historyState = HistoryState.INACTIVE

        self._branches: Dict[int, PipelineHistoryBranch] = dict()

        self._currentBranch: Optional[PipelineHistoryBranch] = None
        self._currentStepID = 0  # Relative to current branch

        self._rootBranch: Optional[PipelineHistoryBranch] = None

        self._uniqueBranchIDCounter = 0

    def initialize(self):
        # Create initial branch

        initialID = self._stepBranchCounter()
        self._currentBranch = PipelineHistoryBranch(initialID)
        self._currentStepID = 0
        self._branches[initialID] = self._currentBranch

        self._rootBranch = self._currentBranch

    def shutdown(self):
        self._historyState = HistoryState.INACTIVE

    def reset(self):
        self._branches.clear()
        self._currentBranch = None
        self._rootBranch = None
        self._currentStepID = 0
        self._uniqueBranchIDCounter = 0

    def registerStep(self, step: DebugStep) -> int:
        self._currentStepID = self._currentBranch.registerStep(step)

        return self._currentStepID

    def traverseToStep(self, stepID: int, branchID: int):
        targetBranch = self._branches.get(branchID, None)

        if targetBranch is None:
            printWarning("Target branch " + str(branchID) + " not found!")
            return None

        if targetBranch != self._currentBranch:
            self._switchBranch(targetBranch)

        self._reachBranchStep(stepID)

    def removeOldestStep(self) -> Optional[List[DebugStep]]:
        if self._rootBranch is None:
            return None

        # If we are currently at the first step of the root branch it's not possible to remove it
        if (self._rootBranch == self._currentBranch and
                self._currentStepID == self._currentBranch.getFirstStep().localID):
            return None

        removeRes = self._rootBranch.removeFirstStep()

        if removeRes is None:  # Empty branch, should never happen
            return None

        # The graph struc changed if the root branch lost its parent or a child
        # If the root branch is now empty, a child was lost and it triggers an update
        changedBranchStruct = (removeRes.removedParentBranch is not None
                               or removeRes.removedChildBranches is not None)

        removedSteps = [removeRes.removedStep]

        if not changedBranchStruct:
            self._debugger.onHistoryBranchUpdate(self._rootBranch)

            return removedSteps

        # Now we should check from our current position what branches we still reach and clear all other, adapt rootBranch

        newRoot = self._currentBranch.findRootBranch()
        newBranches = self._discoverBranches(newRoot)

        removedBranches = [self._branches[b] for b in self._branches if b not in newBranches]

        for rem in removedBranches:
            removedSteps.extend(rem.getAllSteps())
            rem.clearSteps()

            self._debugger.onHistoryBranchUpdate(rem)

        self._branches = newBranches
        self._rootBranch = newRoot

        return removedSteps

    def onHistoryActivated(self):
        self._historyState = HistoryState.ACTIVE

    def onHistoryDeactivated(self):
        # If we continue the history from a different position than the last we need to create a new branch

        if self._currentBranch.getStepCount() > 0 and self._currentStepID != self._currentBranch.getLastStep().localID:
            splitStepID = self._currentStepID
            splitStep = self._currentBranch.getStep(self._currentStepID)

            self._currentBranch = self._createBranchSplit()
            self._currentStepID = 0

            self._debugger.getServerManager().sendSocketData(json.dumps({"cmd": "debSplit",
                                                                         "branchID": self._currentBranch.id,
                                                                         "parentID": self._currentBranch.parentBranch.id,
                                                                         "splitTime": splitStep.time,
                                                                         "splitStep": splitStepID}))

        # Notify operators

        pipeline = getRuntimeManager().getPipeline()

        for op in pipeline.getAllOperators():
            op.getDebugger().continueHistory()

        self._historyState = HistoryState.INACTIVE

    # ----------------------- GETTER -----------------------

    def findClosestStepForTime(self, branchID: int, targetTime: float) -> Optional[DebugStep]:
        branch = self._branches.get(branchID, None)

        if branch is None:
            return None

        lowerStep = None
        higherStep = None

        for step in branch.getAllSteps():
            if step.time <= targetTime:
                lowerStep = step
            else:
                higherStep = step

                break

        if lowerStep is None and higherStep is None:
            return None
        elif lowerStep is None:
            return higherStep
        elif higherStep is None:
            return lowerStep

        lowerDif = abs(targetTime - lowerStep.time)
        higherDif = abs(targetTime - higherStep.time)

        if lowerDif < higherDif:
            return lowerStep
        else:
            return higherStep

    def findAllSteps(self, operatorID: Optional[int] = None, stepType: Optional[DebugStepType] = None,
                     minTime: Optional[float] = None, maxTime: Optional[float] = None,
                     customCheck: Optional[Callable[[DebugStep], bool]] = None) -> List[DebugStep]:
        foundSteps: List[DebugStep] = list()

        for branch in self._branches.values():
            for step in branch.getAllSteps():
                if operatorID is not None and step.debugTuple.debugger.getOperator().id != operatorID:
                    continue

                if stepType is not None and step.type != stepType:
                    continue

                if minTime is not None and step.time < minTime:
                    continue

                if maxTime is not None and step.time > maxTime:
                    continue

                if customCheck is not None and not customCheck(step):
                    continue

                foundSteps.append(step)
        return foundSteps

    def findLastStepOfTypes(self, opID: int, stepTypes: List[DebugStepType], searchParents: bool = True,
                            startStep: Optional[int] = None) -> Dict[DebugStepType, DebugStep]:
        foundSteps: Dict[DebugStepType, DebugStep] = dict()
        openSteps: Set[DebugStepType] = set(stepTypes)

        currentBranch = self._currentBranch
        currentStepID = self._currentStepID if startStep is None else startStep  # If no start step provided take current

        while True:
            if currentBranch.getStepCount() > 0:
                for sID in range(currentStepID, -1, -1):
                    s = currentBranch.getStep(sID)

                    if s.debugger.getOperator().id == opID and s.type in openSteps:
                        foundSteps[s.type] = s
                        openSteps.remove(s.type)

                        if len(openSteps) == 0:
                            return foundSteps

            if currentBranch.parentBranch is None or not searchParents:
                return foundSteps

            currentStepID = currentBranch.parentBranch.getSplitStepIDForChild(currentBranch)
            currentBranch = currentBranch.parentBranch

            if currentStepID is None:
                return foundSteps

    def getHistoryStartTime(self) -> float:
        if self._rootBranch is None:
            return 0

        firstStep = self._rootBranch.getFirstStep()

        if firstStep is None:
            return 0

        return firstStep.time

    def getHistoryState(self) -> HistoryState:
        return self._historyState

    def getMaxStepsForCurrentBranch(self):
        return self._currentBranch.getStepCount() if self._currentBranch is not None else None

    def getFirstStepForCurrentBranch(self) -> Optional[DebugStep]:
        return self._currentBranch.getFirstStep() if self._currentBranch is not None else None

    def getLastStepForCurrentBranch(self) -> Optional[DebugStep]:
        return self._currentBranch.getLastStep() if self._currentBranch is not None else None

    def getCurrentStep(self) -> Optional[DebugStep]:
        return self._currentBranch.getStep(self._currentStepID)

    def getCurrentStepID(self):
        # In very rare cases current ID might be -1 for a short amount of time to signal,
        # that a branch needs to be undone/redone from the beginning
        return max(0, self._currentStepID)

    def getCurrentBranchID(self):
        return self._currentBranch.id if self._currentBranch is not None else None

    def getCurrentBranch(self) -> Optional[PipelineHistoryBranch]:
        return self._currentBranch

    def getBranch(self, branchID: int) -> Optional[PipelineHistoryBranch]:
        return self._branches.get(branchID, None)

    def getAllBranches(self):
        return self._branches.values()

    def getRootBranch(self):
        return self._rootBranch

    # ---------------------- INTERNAL ----------------------

    @staticmethod
    def _discoverBranches(rootBranch: PipelineHistoryBranch):
        # Check which branches can be reached from our starting root branch

        newBranches: Dict[int, PipelineHistoryBranch] = dict()

        queue: Deque[PipelineHistoryBranch] = deque()
        queue.append(rootBranch)

        while queue:
            current = queue.popleft()

            newBranches[current.id] = current

            for children in current.childBranches.values():
                for child in children:
                    queue.append(child)

        return newBranches

    def _reachBranchStep(self, stepID: int, allowCompleteUndo: bool = False):
        # Reaching a step always means to reach to a state where the step has been executed.
        # On undo this means the target step shouldn't be undone, but redone respectively
        # For a branch switch it is important to also undo the very first step (id=0),
        # in this case we can pass -1 as the lower step

        minStep = self._currentBranch.getFirstStep().localID
        if allowCompleteUndo:
            minStep -= 1

        stepV = clamp(stepID, minStep, self._currentBranch.getLastStep().localID)

        if self._currentStepID > stepID:
            self._historyState = HistoryState.TRAVERSING_BACKWARD

            # Start at currentStep because we have to undo it, do not include target step since we want to reach that
            for i in range(self._currentStepID, stepV, -1):
                step = self._currentBranch.getStep(i)

                step.executeUndo(step.prevDebugTuple.getTuple() if step.prevDebugTuple is not None else None,
                                 step.debugTuple.getTuple())

                self._currentStepID = i - 1

                step.debugger.onTraversal(self._currentBranch.getStep(self._currentStepID))  # Update current active step in op debugger

        elif self._currentStepID < stepID:
            self._historyState = HistoryState.TRAVERSING_FORWARD

            # We start at currentStep + 1 because we are at currentStep, no need to redo, include target to redo it
            for i in range(self._currentStepID + 1, stepV + 1, 1):
                step = self._currentBranch.getStep(i)

                step.executeRedo(step.prevDebugTuple.getTuple() if step.prevDebugTuple is not None else None,
                                 step.debugTuple.getTuple())

                self._currentStepID = i

                step.debugger.onTraversal(step)  # Update current active step in op debugger

        self._currentStepID = stepV
        self._historyState = HistoryState.ACTIVE

    def _switchBranch(self, targetBranch: PipelineHistoryBranch):
        path = self.findPath(self._currentBranch, targetBranch)

        for branch in path:
            if branch == self._currentBranch:
                continue

            if branch == self._currentBranch.parentBranch:  # Branch is parent of current branch
                self._reachBranchStep(-1, True)  # Traverse the current branch back to the beginning, also undo very first step

                self._currentStepID = branch.getSplitStepIDForChild(self._currentBranch)
            else:  # Branch is child of current branch
                # Here we never need to undo the complete branch since a split can at minimum occur at stepID=0 (after step was done)
                self._reachBranchStep(self._currentBranch.getSplitStepIDForChild(branch))  # Traverse to the split point

                self._currentStepID = -1  # The first step of the new branch still needs to be redone

            self._currentBranch = branch

    @staticmethod
    def findPath(startBranch: PipelineHistoryBranch, targetBranch: PipelineHistoryBranch) -> List[PipelineHistoryBranch]:
        if startBranch == targetBranch:
            return []

        explored: Set[int] = set()
        queue: List[List[PipelineHistoryBranch]] = [[startBranch]]

        while queue:
            path = queue.pop(0)
            branch = path[-1]  # Last element

            if branch.id not in explored:
                explored.add(branch.id)

                # Collect all neighbour branches (children + parent)

                neighbours = []
                for chd in branch.childBranches.values():
                    neighbours.extend(chd)

                if branch.parentBranch is not None:
                    neighbours.append(branch.parentBranch)

                for neighbour in neighbours:
                    newPath = path.copy()
                    newPath.append(neighbour)

                    queue.append(newPath)  # Add this new variation to queue paths

                    if neighbour == targetBranch:
                        return newPath

    def _createBranchSplit(self) -> PipelineHistoryBranch:
        parentBranch = self._currentBranch

        newBranch = PipelineHistoryBranch(self._stepBranchCounter(), parentBranch)
        parentBranch.addChild(newBranch, self._currentStepID)

        self._branches[newBranch.id] = newBranch

        return newBranch

    def _stepBranchCounter(self) -> int:
        newBranchID = self._uniqueBranchIDCounter
        self._uniqueBranchIDCounter += 1
        return newBranchID
