from __future__ import annotations

from typing import Dict, Set, TYPE_CHECKING, Optional

from spe.runtime.compiler.compileDB import CompileCluster

if TYPE_CHECKING:
    from spe.pipeline.pipeline import Pipeline
    from spe.runtime.compiler.compileDB import CompileDB
    from spe.runtime.compiler.opCompileConfig import OpCompileConfig
    from spe.runtime.compiler.opCompileData import OpCompileData


class CompileClustering:
    def __init__(self, compileDB: CompileDB, pipeline: Pipeline):
        self.compileDB = compileDB
        self.pipeline = pipeline

        self.handledOps: Set[int] = set()

        self.prevClusterCfgs: Dict[int, OpCompileConfig.ClusterConfig] = dict()

    def calculateCluster(self):
        # Calculates a clustering of related operators, which is relevant for the subsequent code generation.
        # Operators belong to the same cluster if they share the same framework and language.

        self._resetPrevClustering()

        # Start clustering for all operators in case of disconnected ops

        for op in self.pipeline.getAllOperators():
            sData = self.compileDB.opCompileData.get(op.id)

            if op.id in self.handledOps:
                continue

            self.handledOps.add(op.id)

            # Unhandled sources start a new cluster

            self._createNewCluster(sData)

            self._clusterNeighbours(sData)

        # Identify and create connections between clusters

        for con in self.pipeline.getAllConnections():
            inOp = self.compileDB.opCompileData[con.input.op.id]
            outOp = self.compileDB.opCompileData[con.output.op.id]

            # Register connections for both clusters

            if inOp.compileConfig.cluster.clusterID != outOp.compileConfig.cluster.clusterID:
                inCluster = self.compileDB.cluster[inOp.compileConfig.cluster.clusterID]
                outCluster = self.compileDB.cluster[outOp.compileConfig.cluster.clusterID]

                CompileCluster.registerConnection(inOp, outOp, inCluster, outCluster, con)

        # Finalize clusters by choosing cluster connection config values for each connection of the ops

        for opD in self.compileDB.opCompileData.values():
            cfg = opD.compileConfig
            cluster = self.compileDB.cluster[cfg.cluster.clusterID]

            for cc in cluster.clusterConnections:
                if not cc.isOperatorInvolved(opD.operator):
                    continue

                if not cc.hasCompatible():
                    continue

                prevValidCfg = self._getPrevValidClusterConnectionCfg(opD, cc)

                if prevValidCfg is not None:
                    opD.compileConfig.cluster.createConnectionConfig(prevValidCfg.conID, prevValidCfg.conType, prevValidCfg.params)
                else:  # Choose first compatible connection cfg as default fallback
                    cfg = cc.compatibleCcs[0]  # First values as default

                    ourSideCfg = cfg.sourceCfg if cc.sourceOp == opD else cfg.sinkCfg

                    opD.compileConfig.cluster.createConnectionConfig(cc.connection.id, ourSideCfg.conType, ourSideCfg.params.copy())

    def _resetPrevClustering(self):
        # Collect previous cluster configs (and cluster connections configs) and clear all

        self.compileDB.cluster.clear()

        for od in self.compileDB.opCompileData.values():
            if od.compileConfig.cluster is not None:
                self.prevClusterCfgs[od.operator.id] = od.compileConfig.cluster

                od.compileConfig.cluster = None

    def _createNewCluster(self, initialOp: OpCompileData) -> CompileCluster:
        newCluster = CompileCluster(len(self.compileDB.cluster))
        self.compileDB.cluster[newCluster.id] = newCluster

        initialOp.compileConfig.setCluster(newCluster)

        return newCluster

    def _getNeighbours(self, opData: OpCompileData):
        for i in opData.operator.inputs:
            for con in i.getConnections():
                nData = self.compileDB.opCompileData.get(con.output.op.id)

                yield con, nData

        for o in opData.operator.outputs:
            for con in o.getConnections():
                nData = self.compileDB.opCompileData.get(con.input.op.id)

                yield con, nData

    def _clusterNeighbours(self, opData: OpCompileData):
        opCfg = opData.compileConfig
        neighbours = self._getNeighbours(opData)

        for n in neighbours:
            nData = n[1]

            nCfg = nData.compileConfig

            if nData.operator.id in self.handledOps:
                continue

            self.handledOps.add(nData.operator.id)

            if opCfg.framework == nCfg.framework:  # Same cluster
                nCfg.setCluster(self.compileDB.cluster[opCfg.cluster.clusterID])
            else:  # New cluster
                self._createNewCluster(nData)

            self._clusterNeighbours(nData)

    def _getPrevValidClusterConnectionCfg(self, op: OpCompileData, con: CompileCluster.ClusterConnection) -> Optional[OpCompileConfig.ClusterConnectionConfig]:
        # Check if we have a previous connection config and if it is still valid (need to check for both sides!)

        sourcePrevCfg = self.prevClusterCfgs.get(con.sourceOp.operator.id)
        sinkPrevCfg = self.prevClusterCfgs.get(con.sinkOp.operator.id)

        if sourcePrevCfg is None or sinkPrevCfg is None:
            return None

        # Check, if both sides have a config for this connection

        sourceConCfg = sourcePrevCfg.getConnectionConfig(con.connection.id)
        sinkConCfg = sinkPrevCfg.getConnectionConfig(con.connection.id)

        if sourceConCfg is None or sinkConCfg is None:
            return None

        # Check if both configs are still supported by the connection

        if not con.isSupported(sourceConCfg, sinkConCfg):
            return None

        return sourceConCfg if con.sourceOp == op else sinkConCfg
