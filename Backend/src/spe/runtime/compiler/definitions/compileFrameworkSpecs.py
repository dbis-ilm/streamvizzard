from __future__ import annotations
from typing import List, Optional, Type, Dict, TYPE_CHECKING, Callable

from spe.runtime.compiler.codegeneration.frameworks.frameworkCompiler import FrameworkCompiler
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkFC import PyFlinkFC
from spe.runtime.compiler.codegeneration.frameworks.streamVizzard.streamVizzardFC import StreamVizzardFC
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileLanguage, CompileComputeMode, \
    CompileParallelism, CompileFrameworkConnector
from spe.runtime.compiler.placement.frameworkAdvisor.pyFlinkFA import PyFlinkFA
from spe.runtime.compiler.placement.frameworkAdvisor.streamVizzardFA import StreamVizzardFA

if TYPE_CHECKING:
    from spe.runtime.compiler.placement.frameworkAdvisor.frameworkAdvisor import FrameworkAdvisor
    from spe.pipeline.operators.operator import Operator


class CompileFrameworkSpecs:
    def __init__(self, framework: CompileFramework, compiler: Type[FrameworkCompiler],
                 supportedLanguages: List[CompileLanguage],
                 supportedParallelism: List[CompileParallelism],
                 supportedComputeModes: List[CompileComputeMode],
                 supportedConnectors: List[FrameworkConnectorCfg],
                 supportsMergedClusters: bool,
                 supportedCheck: Optional[Callable[[Operator], bool]] = None,
                 placementAdvisor: Optional[Type[FrameworkAdvisor]] = None):
        self.framework = framework
        self.compiler = compiler
        self.supportedLanguages = supportedLanguages
        self.supportedParallelism = supportedParallelism
        self.supportedComputeModes = supportedComputeModes

        self._placementAdvisor = placementAdvisor

        # Custom function that may take op inputs/outputs into account to check if it is supported by the framework
        self.supportedCheck = supportedCheck

        self.supportedConnectors = supportedConnectors
        self.supportsMergedClusters = supportsMergedClusters

    def getPlacementAdvisorInstance(self):
        return self._placementAdvisor(self) if self._placementAdvisor is not None else None

    def getConnectorConfig(self, cType: CompileFrameworkConnector, source: bool) -> Optional[FrameworkConnectorCfg]:
        for sCon in self.supportedConnectors:
            if sCon.conType == cType and (source and sCon.supportsSource or not source and sCon.supportsSink):
                return sCon

        return None

    @staticmethod
    def getCompatibleConnectors(sourceFw: CompileFrameworkSpecs, sinkFw: CompileFrameworkSpecs) -> List[FrameworkConnectorCfg.Pair]:
        comp: List[FrameworkConnectorCfg.Pair] = []

        # Find a suitable pair of compatible connectors for the own and the other framework

        for sCon in sourceFw.supportedConnectors:
            if not sCon.supportsSource:
                continue

            for s in sCon.conType.getCompatible():
                # Check if sink has one of our supported connectors
                otherCon = next((elm for elm in sinkFw.supportedConnectors if elm.conType == s), None)

                if otherCon is None or not otherCon.supportsSink:
                    continue

                comp.append(FrameworkConnectorCfg.Pair(sCon, otherCon))

        return comp


class FrameworkConnectorCfg:
    """ Configuration for the connector. If compatible connectors for the
    other side have same param names, they will be set to same value in ui. """

    def __init__(self, conType: CompileFrameworkConnector, supportsSource: bool, supportsSink: bool, params: Dict, maxParallelism: Optional[int]):
        self.conType = conType
        self.params = params
        self.maxParallelism = maxParallelism
        self.supportsSource = supportsSource
        self.supportsSink = supportsSink

    class Pair:
        def __init__(self, sourceCfg: FrameworkConnectorCfg, sinkCfg: FrameworkConnectorCfg):
            self.sourceCfg = sourceCfg
            self.sinkCfg = sinkCfg


def _flinkSupportedCheck(op: Operator) -> bool:
    # No ops supported with more than two inputs
    return len(op.inputs) <= 2


textSocketConnectorParams = {"port": "9000", "ip": "127.0.0.1", "delimiter": "\n"}
kafkaConnectorParams = {"broker": "127.0.0.1", "port": "9092", "topic": "my-topic"}


__frameworks = [CompileFrameworkSpecs(CompileFramework.STREAMVIZZARD, StreamVizzardFC,
                                      [CompileLanguage.PYTHON],
                                      [CompileParallelism.SINGLE_NODE],
                                      [CompileComputeMode.CPU],
                                      [
                                          FrameworkConnectorCfg(CompileFrameworkConnector.SOCKET_TEXT_SERVER, True, True,
                                                                textSocketConnectorParams, 1),
                                          FrameworkConnectorCfg(CompileFrameworkConnector.APACHE_KAFKA, True, True,
                                                                kafkaConnectorParams, None)
                                      ], True, placementAdvisor=StreamVizzardFA),

                CompileFrameworkSpecs(CompileFramework.PYFLINK, PyFlinkFC,
                                      [CompileLanguage.PYTHON],
                                      [CompileParallelism.SINGLE_NODE, CompileParallelism.DISTRIBUTED],
                                      [CompileComputeMode.CPU, CompileComputeMode.GPU],
                                      [
                                          FrameworkConnectorCfg(CompileFrameworkConnector.APACHE_KAFKA, True, True,
                                                                kafkaConnectorParams, None)
                                      ], True, supportedCheck=_flinkSupportedCheck, placementAdvisor=PyFlinkFA)]


def getSupportedFrameworks() -> List[CompileFrameworkSpecs]:
    return __frameworks


def getSupportedFramework(env: CompileFramework) -> Optional[CompileFrameworkSpecs]:
    for se in __frameworks:
        if se.framework == env:
            return se
    return None
