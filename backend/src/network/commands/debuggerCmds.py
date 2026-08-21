from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict

from network.commands.commands import Command, CommandRes

if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger
    from network.server import NetworkMode


def applyDebuggerConfig(debugger: PipelineDebugger, data: Dict):
    debugger.changeDebuggerConfig(data.get("enabled", False),
                                  data.get("debuggerMemoryLimit", None),
                                  data.get("debuggerStorageLimit", None),
                                  data.get("historyRewindSpeed", 1),
                                  data.get("historyRewindUseStepTime", True),
                                  data.get("provenanceEnabled", False),
                                  data.get("provenanceAwaitUpdates", True))


class ChangeDebuggerStateCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("changeDebuggerState", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if rm.gateway.getDebugger() is not None:
            rm.gateway.getDebugger().changeDebuggerState(data["historyActive"], data["historyRewind"])

            return CommandRes.ok()

        return CommandRes.error("Debugger not enabled!")


class ChangeDebuggerConfigCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("changeDebuggerConfig", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if rm.gateway.getDebugger() is not None:
            applyDebuggerConfig(rm.gateway.getDebugger(), data)

            return CommandRes.ok()

        return CommandRes.error("Debugger not enabled!")


class DebuggerStepChange(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("debuggerStepChange", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if rm.gateway.getDebugger() is not None:
            rm.gateway.getDebugger().changeDebuggerStep(data["targetStep"], data["targetBranch"])

            return CommandRes.ok()

        return CommandRes.error("Debugger not enabled!")


class RequestDebuggerStepCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("requestDebuggerStep", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if rm.gateway.getDebugger() is not None:
            res = rm.gateway.getDebugger().requestDebuggerStep(data["targetBranch"], data["targetTime"])

            return CommandRes.okWithRes(json.dumps(res)) if res is not None else CommandRes.error("Invalid debugging state!")

        return CommandRes.error("Debugger not enabled!")


class ExecuteProvQueryCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("executeProvenanceQuery", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if rm.gateway.getDebugger() is not None:
            rm.gateway.getDebugger().executeProvenanceQuery(data)

            return CommandRes.ok()

        return CommandRes.error("Debugger not enabled!")
