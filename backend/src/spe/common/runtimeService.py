from __future__ import annotations
import abc

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from network.server import ServerManager
    from spe.runtime.runtimeManager import RuntimeManager


class RuntimeService(abc.ABC):
    def __init__(self, runtimeManager: RuntimeManager, serverManager: ServerManager):
        self.runtimeManager = runtimeManager
        self.serverManager = serverManager

    def onPipelineStarting(self):
        ...

    def onPipelineStopping(self):
        ...

    def onPipelineStopped(self):
        ...

    def onRuntimeShutdown(self):
        ...  # Called when the system stops

    def isPipelineRunning(self) -> bool:
        return self.runtimeManager.isRunning()

    def getPipeline(self):
        return self.runtimeManager.getPipeline()
