from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict, List

from network.commands.commands import Command, CommandRes
from network.commands.debuggerCmds import applyDebuggerConfig
from network.commands.monitorCmds import applyMonitorConfig
from spe.pipeline.pipelineManager import PipelineManager
from spe.pipeline.pipelineUpdates import PipelineUpdate


if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.advisor.pipelineAdvisor import PipelineAdvisor
    from network.server import NetworkMode


def applyAdvisorConfig(advisor: PipelineAdvisor, data: Dict):
    advisor.toggleAdvisor(data.get("enabled", False))


def _applyStartConfig(runtimeManager: RuntimeManager, data: Dict):
    advisor = runtimeManager.gateway.getAdvisor()
    if advisor is not None:
        applyAdvisorConfig(advisor, data.get("advisor", {}))

    monitor = runtimeManager.gateway.getMonitor()
    if monitor is not None:
        applyMonitorConfig(monitor, data.get("monitor", {}))

    debugger = runtimeManager.gateway.getDebugger()
    if debugger is not None:
        applyDebuggerConfig(debugger, data.get("debugger", {}))

        debugger.changeDebuggerState(False, None)


class StartPipelineCMD(Command):
    """ Accepts either the json 'pipeline' data to execute or a 'path' to a pipeline UI savefile. """

    def __init__(self, networkMode: NetworkMode):
        super().__init__("startPipeline", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if "pipeline" in data:
            pipelineRes = PipelineManager.createPipeline(data["pipeline"])

        elif "path" in data:
            try:
                with open(data["path"], "r") as f:
                    pipelineRes = PipelineManager.createPipelineFromUISaveFile(json.load(f))
            except Exception as e:
                print(e)

                return CommandRes.error(f"Failed to read pipeline file {data['path']}!")

        else:
            return CommandRes.error("Missing 'path' or 'pipeline' data values!")

        if pipelineRes.hasError():
            return CommandRes.error(pipelineRes.errorMsg)

        startRes = rm.startPipeline(pipelineRes.pipeline, lambda: _applyStartConfig(rm, data))

        if startRes.hasError():
            return CommandRes.error(startRes.errorMsg)

        return CommandRes.ok()


class StopPipelineCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("stopPipeline", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        rm.stopPipeline()

        return CommandRes.ok()


class UpdatePipelineCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("pipelineUpdate", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        updateID = data["updateID"]
        updates: List[PipelineUpdate] = list()

        for d in data["updates"]:
            upData = PipelineUpdate.parse(d, updateID)

            if upData is not None:
                updates.append(upData)

        rm.updatePipeline(updates)

        return CommandRes.ok()


class ChangeAdvisorConfigCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("changeAdvisorConfig", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if rm.gateway.getAdvisor() is not None:
            applyAdvisorConfig(rm.gateway.getAdvisor(), data)

            return CommandRes.ok()

        return CommandRes.error("Advisor not enabled!")


class SimulateCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("simulate", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        runtimeData = data["runtimeConfig"]
        simulationData = data["simulateData"]

        pipelineRes = PipelineManager.createPipeline(runtimeData["pipeline"])

        if pipelineRes.hasError():
            return CommandRes.error(pipelineRes.errorMsg)

        from spe.runtime.simulation.pipelineSimulation import PipelineSimulation, PipelineSimulationMode

        sim = PipelineSimulation(pipelineRes.pipeline, rm)
        sim.start(simulationData["duration"], PipelineSimulationMode.parse(simulationData["mode"]),
                  simulationData["sources"],
                  simulationData["metaData"], lambda: _applyStartConfig(rm, runtimeData))

        return CommandRes.ok()
