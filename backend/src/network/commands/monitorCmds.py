from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from network.commands.commands import Command, CommandRes

if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.monitor.pipelineMonitor import PipelineMonitor
    from network.server import NetworkMode


def applyMonitorConfig(monitor: PipelineMonitor, data: Dict):
    monitor.changeConfig(data.get("enabled", False), data.get("trackStats", False))


class ChangeMonitorConfigCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("changeMonitorConfig", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if rm.gateway.getMonitor() is not None:
            applyMonitorConfig(rm.gateway.getMonitor(), data)

            return CommandRes.ok()

        return CommandRes.error("Monitor not enabled!")
