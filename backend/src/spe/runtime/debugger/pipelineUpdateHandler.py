from __future__ import annotations

import json
from typing import TYPE_CHECKING, List, Set

from spe.pipeline.pipeline import Pipeline
from spe.pipeline.pipelineUpdates import PipelineUpdate
from spe.runtime.debugger.debugStep import DebugStep

if TYPE_CHECKING:
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger


class PipelineUpdateHandler:
    def __init__(self, debugger: PipelineDebugger):
        self._debugger = debugger

        # Update events are tracked and added to the next registered DS
        # In case of a branch split this will be the first step of the new branch
        # In case the execution is paused or history is traversed, all pending events are removed

        self._pendingEvents: List[PipelineUpdate] = list()

    def start(self, pipeline: Pipeline):
        # Setup listener
        pipeline.getEventListener().register(Pipeline.EVENT_PIPELINE_PRE_UPDATED, self._onPipelineUpdated)

    def onPauseExecution(self):
        # When we pause execution (for traversal) and still have pending events, undo them

        self._undoPendingEvents()

    def onDebugStepRegistered(self, ds: DebugStep):
        # If we have pending events we need to register them on the first following step

        if len(self._pendingEvents) > 0:
            registeredUpdateIDs: Set[int] = set()

            for up in self._pendingEvents:
                ds.registerPipelineUpdate(up)
                registeredUpdateIDs.add(up.updateID)

            self._debugger.getServerManager().sendSocketData(json.dumps({"cmd": "debRegPU",
                                                                         "updateIDs": list(registeredUpdateIDs),
                                                                         "branchID": ds.branchID,
                                                                         "stepID": ds.localID,
                                                                         "stepTime": ds.time}))
            self._pendingEvents.clear()

    def onDebugStepExecuted(self):
        # In this case we manually traverse history and need to undo pending events since they are not bound to a DS

        self._undoPendingEvents()

    def reset(self):
        self._pendingEvents.clear()

    def _onPipelineUpdated(self, up: PipelineUpdate):
        if not up.isTracked():
            return

        self._pendingEvents.append(up)

    def _undoPendingEvents(self):
        if len(self._pendingEvents) == 0:
            return

        # Undo and remove all pending events in reversed order

        registeredUpdateIDs: Set[int] = set()

        for up in self._pendingEvents:
            registeredUpdateIDs.add(up.updateID)

        self._debugger.getServerManager().sendSocketData(json.dumps({"cmd": "debUndoPendingPU",
                                                                     "updateIDs": list(registeredUpdateIDs)}))
        for up in reversed(self._pendingEvents):
            up.undo()

        self._pendingEvents.clear()
