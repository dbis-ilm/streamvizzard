from __future__ import annotations

import json
from typing import Dict, Optional

from network.commands.commands import Command
from spe.pipeline.pipelineManager import PipelineManager
from spe.runtime.runtimeManager import RuntimeManager


class CompileModeStartCMD(Command):
    def __init__(self):
        super().__init__("compileStart")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional[str]:
        pipeData = data["pipeline"]
        pipelineRes = PipelineManager.createPipeline(pipeData)

        if pipelineRes.hasError():
            return json.dumps({"res": False, "error": pipelineRes.errorMsg})

        rm.gateway.getCompiler().startCompileMode(pipelineRes.pipeline)

        return json.dumps({"res": True, "error": None})


class CompileAnalyzeCMD(Command):
    def __init__(self):
        super().__init__("compileAnalyze")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional[str]:
        compileConfigs = data["compileConfigs"]
        strategyData = data["strategy"]

        return json.dumps(
            rm.gateway.getCompiler().calculateTargetSuggestions(strategyData, compileConfigs),
            default=vars)


class CompilePipelineCMD(Command):
    def __init__(self):
        super().__init__("compilePipeline")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> str:
        res = rm.gateway.getCompiler().compilePipeline(data["opCompileConfigs"], data["compileConfig"])

        return json.dumps(res.toJSON())


class CompileModeEndCMD(Command):
    def __init__(self):
        super().__init__("compileEnd")

    def handleCommand(self, rm: RuntimeManager, data: Dict):
        rm.gateway.getCompiler().endCompileMode()
