from __future__ import annotations

import json
from typing import Optional, List
from typing import TYPE_CHECKING

from spe.common.runtimeService import RuntimeService
from streamVizzard import StreamVizzard

if TYPE_CHECKING:
    from network.server import ServerManager
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger
    from spe.runtime.monitor.pipelineMonitor import PipelineMonitor
    from spe.runtime.compiler.pipelineCompiler import PipelineCompiler
    from spe.runtime.advisor.pipelineAdvisor import PipelineAdvisor


class RuntimeGateway:
    def __init__(self, serverManager: ServerManager, runtimeManager: RuntimeManager):
        self._serverManager: Optional[ServerManager] = serverManager
        self._runtimeManager: Optional[RuntimeManager] = runtimeManager

        self._services: List[RuntimeService] = []

        self._monitor: Optional[PipelineMonitor] = None
        self._advisor: Optional[PipelineAdvisor] = None
        self._debugger: Optional[PipelineDebugger] = None
        self._compiler: Optional[PipelineCompiler] = None

        if StreamVizzard.getConfig().MONITORING_ENABLED:
            from spe.runtime.monitor.pipelineMonitor import PipelineMonitor
            self._monitor = PipelineMonitor(self._runtimeManager, self._serverManager)
            self._services.append(self._monitor)

        if StreamVizzard.getConfig().ADVISOR_ENABLED:
            from spe.runtime.advisor.pipelineAdvisor import PipelineAdvisor
            self._advisor = PipelineAdvisor(self._runtimeManager, self._serverManager)
            self._services.append(self._advisor)

        if StreamVizzard.getConfig().DEBUGGER_ENABLED:
            from spe.runtime.debugger.pipelineDebugger import PipelineDebugger
            self._debugger = PipelineDebugger(self._runtimeManager, self._serverManager)
            self._services.append(self._debugger)

        if StreamVizzard.getConfig().COMPILER_ENABLED:
            from spe.runtime.compiler.pipelineCompiler import PipelineCompiler
            self._compiler = PipelineCompiler(self._runtimeManager, self._serverManager)
            self._services.append(self._compiler)

        global _instance
        _instance = self

    def onPipelineStarting(self):
        self._serverManager.sendSocketData(json.dumps({"cmd": "status", "status": "starting"}))

        for service in self._services:
            service.onPipelineStarting()

    def onPipelineStarted(self):
        self._serverManager.sendSocketData(json.dumps({"cmd": "status", "status": "started"}))

    def onPipelineStopping(self):
        for service in self._services:
            service.onPipelineStopping()

        self._serverManager.clearSocketData()

        self._serverManager.sendSocketData(json.dumps({"cmd": "status", "status": "stopping"}))

    def onPipelineStopped(self):
        for service in self._services:
            service.onPipelineStopped()

        from network.socketTuple import GenericSocketTuple
        self._serverManager.sendSocketData(GenericSocketTuple(json.dumps({"cmd": "status", "status": "stopped"}), lambda t: self._serverManager.clearSocketData()))

    def onRuntimeShutdown(self):
        for service in self._services:
            service.onRuntimeShutdown()

    # ---------------- Getter ----------------

    def getDebugger(self) -> Optional[PipelineDebugger]:
        return self._debugger

    def getMonitor(self) -> Optional[PipelineMonitor]:
        return self._monitor

    def getAdvisor(self) -> Optional[PipelineAdvisor]:
        return self._advisor

    def getCompiler(self) -> Optional[PipelineCompiler]:
        return self._compiler

    def getRuntimeManager(self):
        return self._runtimeManager


_instance: RuntimeGateway


def getDebugger() -> Optional[PipelineDebugger]:
    return _instance.getDebugger()


def getRuntimeManager() -> Optional[RuntimeManager]:
    if _instance is not None:
        return _instance.getRuntimeManager()

    return None
