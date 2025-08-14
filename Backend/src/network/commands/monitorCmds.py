from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict

from network.commands.commands import Command

if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.monitor.pipelineMonitor import PipelineMonitor


def applyMonitorConfig(monitor: PipelineMonitor, data: Dict):
    monitor.changeConfig(data.get("enabled", False), data.get("trackStats", False), data.get("heatmapType", 0))


class ChangeMonitorConfigCMD(Command):
    def __init__(self):
        super().__init__("changeMonitorConfig")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional:
        if rm.gateway.getMonitor() is not None:
            applyMonitorConfig(rm.gateway.getMonitor(), data)

        return None
