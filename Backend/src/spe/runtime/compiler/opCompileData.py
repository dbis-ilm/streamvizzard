from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional

from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecsCatalog
from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from spe.runtime.compiler.placement.knowledgeProvider.opKnowledgeProvider import OpKnowledgeProvider
from spe.runtime.compiler.placement.opTargetCatalog import OpTargetStatsEstimation

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.compiler.compileDB import CompileDB
    from spe.runtime.compiler.placement.knowledgeProvider.opKnowledgeProvider import OpKnowledgeType


class OpCompileData:
    def __init__(self, operator: Operator):
        self.operator = operator

        self.specsCatalog = CompileOpSpecsCatalog(operator)

        self.compileConfig = OpCompileConfig()

        self.metaData = OpCompileData.MetaData(operator.getCompileMetaData().inheritTarget)

        self.knowledgeProvider: Dict[OpKnowledgeType, OpKnowledgeProvider] = OpKnowledgeProvider.requestAll(self)

        # Estimated stats from the placement phase for explaining the placement to the user
        self.estimatedTargetStats: Optional[OpTargetStatsEstimation] = None

    def getKnowledgeProvider(self, knowledgeType: OpKnowledgeType):
        return self.knowledgeProvider[knowledgeType]

    def verifyTarget(self) -> bool:
        # Verify that the config is valid and supported by the operator.
        # Update current values with valid values of other conf.

        config = self.compileConfig

        # Reset target if mode is auto or one of the params is missing

        if (config.framework is None
                or config.language is None
                or config.computeMode is None
                or config.parallelism is None):
            config.resetTarget()

        # If op does not support compilation

        if not self.supportsCompilation():
            config.resetTarget()

        # Reset target if it's not supported by the op

        if not self.specsCatalog.verifyOpCompileConfig(config):
            config.resetTarget()

        return config.hasValidTarget()

    def verifyCluster(self, compileDB: CompileDB) -> bool:
        config = self.compileConfig

        # Reset cluster if it was not specified

        if config.cluster is None:
            config.resetCluster()

            return False

        # Reset cluster if it does not exist

        cl = compileDB.cluster.get(config.cluster.clusterID)

        if cl is None:
            config.resetCluster()

            return False

        # Reset cluster if one of the connections (to other clusters) is invalid or missing at all

        for cc in cl.clusterConnections:
            if cc.isOperatorInvolved(self.operator):
                # Cluster has no valid cc at all for this connection, delete from conf but continue

                if not cc.hasCompatible():
                    config.cluster.removeConnectionConfig(cc.connection.id)

                    continue

                # Check, if both sides of the con have a cluster

                if (not cc.sourceOp.compileConfig.hasValidCluster() or
                        not cc.sinkOp.compileConfig.hasValidCluster()):

                    config.resetCluster()

                    return False

                # Check, if both sides of the con have a cluster conf of an existing cluster

                sourceCl = compileDB.cluster.get(cc.sourceOp.compileConfig.cluster.clusterID)
                sinkCl = compileDB.cluster.get(cc.sinkOp.compileConfig.cluster.clusterID)

                if sourceCl is None or sinkCl is None:
                    config.resetCluster()

                    return False

                # Check, if both sides of the connector have a conf for this connection

                sourceConCfg = cc.sourceOp.compileConfig.cluster.getConnectionConfig(cc.connection.id)
                sinkConCfg = cc.sinkOp.compileConfig.cluster.getConnectionConfig(cc.connection.id)

                if sourceConCfg is None or sinkConCfg is None:
                    config.resetCluster()

                    return False

                # Check, if the config of both sides is valid for this connection

                if not cc.isSupported(sourceConCfg, sinkConCfg):
                    config.resetCluster()

                    return False

        return True

    def supportsCompilation(self) -> bool:
        return len(self.specsCatalog.frameworks) > 0

    def reorderTuples(self):
        return self.metaData.canRestoreOutOfOrder and self.compileConfig.enforceTupleOrder

    class MetaData:
        class OutOfOrderCause(Enum):
            JOIN = "Join"  # If operators are joined with different parallelism -> leads to out-of-order combinations
            SOURCE = "Source"
            WINDOW = "Window"
            INPUT_PARA = "InputPara"

        def __init__(self, inheritTarget: bool):
            self.inheritTarget = inheritTarget

            # If the operator might process its data out of order
            self.outOfOrderProcessing = False

            self.outOfOrderCause: Optional[OpCompileData.MetaData.OutOfOrderCause] = None

            # If a reordering operator can be added to restore the order.
            self.canRestoreOutOfOrder = False

        def toJSON(self) -> Dict:
            return {"inheritTarget": self.inheritTarget, "outOfOrderProcessing": self.outOfOrderProcessing,
                    "canRestoreOutOfOrder": self.canRestoreOutOfOrder,
                    "outOfOrderCause": self.outOfOrderCause.value if self.outOfOrderCause is not None else None}
