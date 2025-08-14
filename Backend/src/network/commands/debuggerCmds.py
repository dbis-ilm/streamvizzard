from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Dict

from network.commands.commands import Command


if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger


# TODO: We could replace all json data objects with serializable classes for better maintainability

def applyDebuggerConfig(debugger: PipelineDebugger, data: Dict):
    debugger.changeDebuggerConfig(data.get("enabled", False),
                                  data.get("debuggerMemoryLimit", None),
                                  data.get("debuggerStorageLimit", None),
                                  data.get("historyRewindSpeed", 1),
                                  data.get("historyRewindUseStepTime", True),
                                  data.get("provenanceEnabled", False),
                                  data.get("provenanceAwaitUpdates", True))


class ChangeDebuggerStateCMD(Command):
    def __init__(self):
        super().__init__("changeDebuggerState")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional:
        if rm.gateway.getDebugger() is not None:
            rm.gateway.getDebugger().changeDebuggerState(data["historyActive"], data["historyRewind"])

        return None


class ChangeDebuggerConfigCMD(Command):
    def __init__(self):
        super().__init__("changeDebuggerConfig")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional:
        if rm.gateway.getDebugger() is not None:
            applyDebuggerConfig(rm.gateway.getDebugger(), data)

        return None


class DebuggerStepChange(Command):
    def __init__(self):
        super().__init__("debuggerStepChange")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional:
        if rm.gateway.getDebugger() is not None:
            rm.gateway.getDebugger().changeDebuggerStep(data["targetStep"], data["targetBranch"])

        return None


class RequestDebuggerStepCMD(Command):
    def __init__(self):
        super().__init__("requestDebuggerStep")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional[str]:
        if rm.gateway.getDebugger() is not None:
            return json.dumps(
                rm.gateway.getDebugger().requestDebuggerStep(data["targetBranch"], data["targetTime"]))

        return json.dumps(None)


class ExecuteProvQueryCMD(Command):
    def __init__(self):
        super().__init__("executeProvenanceQuery")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional:
        if rm.gateway.getDebugger() is not None:
            rm.gateway.getDebugger().executeProvenanceQuery(data)

        return None
