from __future__ import annotations
from typing import Dict, List, TYPE_CHECKING, Optional

from spe.pipeline.connection import Connection
from spe.runtime.compiler.definitions.compileFrameworkSpecs import getSupportedFramework, CompileFrameworkSpecs
from utils.utils import escapeStrInDict

if TYPE_CHECKING:
    from spe.runtime.compiler.opCompileData import OpCompileData
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.compiler.opCompileConfig import OpCompileConfig


class CompileDB:
    def __init__(self):
        # This data is persistent during the compiler session!

        self.opCompileData: Dict[int, OpCompileData] = dict()

        self.cluster: Dict[int, CompileCluster] = dict()


class CompileCluster:
    """ A compile cluster contains connected operators with the same framework and language target. """

    def __init__(self, clusterID: int):
        self.id = clusterID
        self.clusterConnections: List[CompileCluster.ClusterConnection] = list()

    def getClusterConnection(self, con: Connection) -> Optional[ClusterConnection]:
        for cc in self.clusterConnections:
            if cc.connection == con:
                return cc

        return None

    def exportSupportedConnections(self, op: Operator) -> Dict:
        # Exports all supported cluster connections

        ccs = {}

        for cc in self.clusterConnections:
            if not cc.sinkOp.operator == op and not cc.sourceOp.operator == op:
                continue

            ourIsSource = cc.sourceOp.operator == op

            allOptions = cc.compatibleCcs

            options = []

            for o in allOptions:
                entry = {"ourConType": o.sourceCfg.conType.value if ourIsSource else o.sinkCfg.conType.value,
                         "ourConParams": escapeStrInDict(o.sourceCfg.params, True) if ourIsSource else escapeStrInDict(o.sinkCfg.params, True),
                         "otherConType": o.sinkCfg.conType.value if ourIsSource else o.sourceCfg.conType.value}

                options.append(entry)

            ccs[cc.connection.id] = options

        return ccs

    @staticmethod
    def registerConnection(firstOp: OpCompileData, secondOp: OpCompileData,
                           firstCluster: CompileCluster, secondCluster: CompileCluster,
                           connection: Connection):

        if firstCluster == secondCluster:
            return

        ourSocket = connection.input if connection.input.op == firstOp.operator else connection.output

        sourceOp = firstOp if ourSocket.inSocket else secondOp
        sinkOp = secondOp if ourSocket.inSocket else firstOp

        cc = CompileCluster.ClusterConnection(sourceOp, sinkOp, connection)

        firstCluster.clusterConnections.append(cc)
        secondCluster.clusterConnections.append(cc)

    class ClusterConnection:
        def __init__(self, sourceOp: OpCompileData, sinkOp: OpCompileData, connection: Connection):
            self.sourceOp = sourceOp
            self.sinkOp = sinkOp

            self.connection = connection

            sourceFw = getSupportedFramework(self.sourceOp.compileConfig.framework)
            sinkFw = getSupportedFramework(self.sinkOp.compileConfig.framework)

            self.compatibleCcs = CompileFrameworkSpecs.getCompatibleConnectors(sourceFw, sinkFw)

        def hasCompatible(self) -> bool:
            return len(self.compatibleCcs) > 0

        def isOperatorInvolved(self, op: Operator) -> bool:
            return self.sourceOp.operator == op or self.sinkOp.operator == op

        def isSupported(self, sourceCfg: OpCompileConfig.ClusterConnectionConfig,
                        sinkCfg: OpCompileConfig.ClusterConnectionConfig) -> bool:

            # Check if the configs are still present in the list of supported connections

            for compatible in self.compatibleCcs:
                if (compatible.sourceCfg.conType == sourceCfg.conType and
                        compatible.sinkCfg.conType == sinkCfg.conType):

                    # Check if all params are contained
                    return (compatible.sourceCfg.params.keys() <= sourceCfg.params.keys() and
                            compatible.sinkCfg.params.keys() <= sinkCfg.params.keys())

            return False
