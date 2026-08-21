from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from network.commands.commands import Command, CommandRes
from spe.pipeline.pipelineManager import PipelineManager

if TYPE_CHECKING:
    from network.server import NetworkMode
    from spe.runtime.runtimeManager import RuntimeManager


class CompileModeStartCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("compileStart", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if (compiler := rm.gateway.getCompiler()) is not None:
            pipeData = data["pipeline"]
            pipelineRes = PipelineManager.createPipeline(pipeData)

            if pipelineRes.hasError():
                return CommandRes.error(pipelineRes.errorMsg)

            compiler.startCompileMode(pipelineRes.pipeline)

            return CommandRes.ok()

        return CommandRes.error("Compiler not enabled!")


class CompileAnalyzeCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("compileAnalyze", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if (compiler := rm.gateway.getCompiler()) is not None:
            compileConfigs = data["compileConfigs"]
            strategyData = data["strategy"]

            res = compiler.calculateTargetSuggestions(strategyData, compileConfigs)

            return CommandRes.error(res.errorMsg) if res.hasError() else CommandRes.okWithRes(res.result)

        return CommandRes.error("Compiler not enabled!")


class CompilePipelineCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("compilePipeline", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if (compiler := rm.gateway.getCompiler()) is not None:
            res = compiler.compilePipeline(data["opCompileConfigs"], data["compileConfig"])

            return CommandRes.error(res.errorMsg) if res.hasError() else CommandRes.okWithRes(res.result)

        return CommandRes.error("Compiler not enabled!")


class CompileModeEndCMD(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("compileEnd", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        if (compiler := rm.gateway.getCompiler()) is not None:
            compiler.endCompileMode()

            return CommandRes.ok()

        return CommandRes.error("Compiler not enabled!")
