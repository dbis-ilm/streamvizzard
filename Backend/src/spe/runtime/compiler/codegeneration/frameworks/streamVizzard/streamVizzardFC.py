from __future__ import annotations

import json
import logging
import os
import textwrap
import traceback
from typing import TYPE_CHECKING

from spe.pipeline.connection import Connection
from spe.pipeline.socket import Socket
from spe.runtime.compiler.compilerRes import CompilerRes
from spe.runtime.compiler.codegeneration.frameworks.frameworkCompiler import FrameworkCompiler
from spe.runtime.compiler.definitions.compileDefinitions import CompileFrameworkConnector, CompileLanguage
from spe.runtime.compiler.opCompileConfig import OpCompileConfig

if TYPE_CHECKING:
    from spe.runtime.compiler.definitions.compileFrameworkSpecs import CompileFrameworkSpecs
    from spe.runtime.compiler.codegeneration.codeGenerator import CodeGenerator


class StreamVizzardFC(FrameworkCompiler):
    def __init__(self, framework: CompileFrameworkSpecs, clusterID: int, generator: CodeGenerator):
        super().__init__(framework, clusterID, generator)

    def generateCode(self) -> CompilerRes:
        opData = [op.operator.exportOperatorData() for op in self.opNodes]

        pipelineData = {"operators": opData}

        from spe.pipeline.pipelineManager import PipelineManager
        pipelineRes = PipelineManager.createPipeline(pipelineData)

        if pipelineRes.hasError():
            return CompilerRes(f"Couldn't generate StreamVizzard pipeline!\n {pipelineRes.errorMsg}")

        pipelineUISaveFile = PipelineManager.generateUISaveFile(pipelineRes.pipeline)

        outputFolder = os.path.join(self.generator.getOutputPath(), "StreamVizzard_" + str(self.clusterID))
        os.makedirs(outputFolder, exist_ok=True)

        # Write UI save file for running from editor / cli

        try:
            with open(os.path.join(outputFolder, "pipeline.json"), "w") as f:
                f.write(json.dumps(pipelineUISaveFile))
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return CompilerRes("Failed to save pipeline UI file!")

        # Write README

        try:
            with open(os.path.join(outputFolder, "readme.md"), "w") as f:
                f.write(textwrap.dedent("""
                    Usage Options:
                    1) Load the pipeline.json file with the Web-Editor to execute the pipeline
                    2) Run the cli (src/cli.py) with the 'startPipeline' subcommand and the pipeline.json as the file path
                       For docker setups, the cli can be reached with docker exec -it svbackend svcli
                    """).strip())
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return CompilerRes("Failed to save readme file!")

        return CompilerRes.ok()

    def registerConnector(self, cc: OpCompileConfig.ClusterConnectionConfig, con: Connection, socket: Socket) -> CompilerRes:
        # Find code generator for the connector

        if cc.conType == CompileFrameworkConnector.SOCKET_TEXT_SERVER:
            # TODO: ADD
            ...
        elif cc.conType == CompileFrameworkConnector.APACHE_KAFKA:
            return self._generateKafkaConnector(cc, socket, CompileLanguage.PYTHON)

        return CompilerRes(f"No SV connector implementation found for {cc.conType}")

    def mergeWith(self, otherCp: StreamVizzardFC) -> bool:
        for op in otherCp.opNodes:
            self.registerOperator(op)

        return True
