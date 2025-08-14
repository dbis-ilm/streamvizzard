from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Dict, List

from network.commands.commands import Command
from network.commands.debuggerCmds import applyDebuggerConfig
from network.commands.monitorCmds import applyMonitorConfig
from spe.pipeline.pipelineManager import PipelineManager
from spe.pipeline.pipelineUpdates import PipelineUpdate


if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from spe.runtime.advisor.pipelineAdvisor import PipelineAdvisor


# TODO: We could replace all json data objects with serializable classes for better maintainability

def applyAdvisorConfig(advisor: PipelineAdvisor, data: Dict):
    advisor.toggleAdvisor(data.get("enabled", False))


def _applyStartMetaData(runtimeManager: RuntimeManager, metaData: Optional[Dict]):
    if metaData is None:
        metaData = {}

    advisor = runtimeManager.gateway.getAdvisor()
    if advisor is not None:
        applyAdvisorConfig(advisor, metaData.get("advisor", {}))

    monitor = runtimeManager.gateway.getMonitor()
    if monitor is not None:
        applyMonitorConfig(monitor, metaData.get("monitor", {}))

    debugger = runtimeManager.gateway.getDebugger()
    if debugger is not None:
        applyDebuggerConfig(debugger, metaData.get("debugger", {}))

        debugger.changeDebuggerState(False, None)


class StartPipelineCMD(Command):
    """ Accepts either the json 'pipeline' data to execute or a 'path' to a pipeline UI savefile. """

    def __init__(self):
        super().__init__("startPipeline")

    @staticmethod
    def error(errorMsg: str) -> str:
        return json.dumps({"res": False, "error": errorMsg})

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional[str]:
        if "pipeline" in data:
            pipelineRes = PipelineManager.createPipeline(data["pipeline"])

        elif "path" in data:
            try:
                with open(data["path"], "r") as f:
                    pipelineRes = PipelineManager.createPipelineFromUISaveFile(json.load(f))
            except Exception:
                return self.error(f"Failed to read pipeline file {data['path']}!")

        else:
            return self.error("Missing 'path' or 'pipeline' data values!")

        if pipelineRes.hasError():
            return self.error(pipelineRes.errorMsg)

        startRes = rm.startPipeline(pipelineRes.pipeline, lambda: _applyStartMetaData(rm, data.get("meta")))

        return json.dumps({"res": not startRes.hasError(), "error": startRes.errorMsg})


class StopPipelineCMD(Command):
    def __init__(self):
        super().__init__("stopPipeline")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional:
        rm.stopPipeline()

        return None


class UpdatePipelineCMD(Command):
    def __init__(self):
        super().__init__("pipelineUpdate")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional:
        updateID = data["updateID"]
        updates: List[PipelineUpdate] = list()

        for d in data["updates"]:
            upData = PipelineUpdate.parse(d, updateID)

            if upData is not None:
                updates.append(upData)

        rm.updatePipeline(updates)

        return None


class ChangeAdvisorConfigCMD(Command):
    def __init__(self):
        super().__init__("changeAdvisorConfig")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional:
        if rm.gateway.getAdvisor() is not None:
            applyAdvisorConfig(rm.gateway.getAdvisor(), data)

        return None


class SimulateCMD(Command):
    def __init__(self):
        super().__init__("simulate")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional[str]:
        pipeData = data["pipeline"]
        simulationData = data["simulateData"]

        pipelineRes = PipelineManager.createPipeline(pipeData)

        if pipelineRes.hasError():
            return json.dumps({"res": False, "error": pipelineRes.errorMsg})

        from spe.runtime.simulation.pipelineSimulation import PipelineSimulation, PipelineSimulationMode

        sim = PipelineSimulation(pipelineRes.pipeline, rm)
        sim.start(simulationData["duration"], PipelineSimulationMode.parse(simulationData["mode"]),
                  simulationData["sources"],
                  simulationData["metaData"], lambda: _applyStartMetaData(rm, data["meta"]))

        return json.dumps({"res": True, "error": None})
