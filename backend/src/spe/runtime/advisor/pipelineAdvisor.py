import json
from typing import List

from network.server import ServerManager
from spe.pipeline.operators.operator import Operator
from spe.runtime.advisor.advisorSuggestion import AdvisorSuggestion
from spe.runtime.runtimeManager import RuntimeManager
from spe.common.runtimeService import RuntimeService


class PipelineAdvisor(RuntimeService):
    def __init__(self, runtimeManager: RuntimeManager, serverManager: ServerManager):
        super().__init__(runtimeManager, serverManager)

        self._enabled = False

    def onAdvisorSuggestion(self, operator: Operator, advisorSuggestions: List[AdvisorSuggestion]):
        if not self.isPipelineRunning():
            return

        data = {"cmd": "opAdvisorSug", "opID": operator.id}

        suggestions = []

        for sug in advisorSuggestions:
            suggestions.append(sug.getData())

        data["sugs"] = suggestions if len(suggestions) > 0 else None

        self.serverManager.sendSocketData(json.dumps(data))

    def toggleAdvisor(self, enabled: bool):
        self._enabled = enabled

    def isEnabled(self) -> bool:
        return self._enabled
