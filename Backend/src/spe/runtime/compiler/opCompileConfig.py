from __future__ import annotations

from typing import Optional, Dict, TYPE_CHECKING

from spe.runtime.compiler.definitions.compileDefinitions import CompileLanguage, CompileParallelism, CompileComputeMode, \
    CompileFramework, CompileFrameworkConnector
from utils.utils import escapeStrInDict, tryParseFloat, tryParseInt

if TYPE_CHECKING:
    from spe.runtime.compiler.compileDB import CompileCluster


class OpCompileConfig:
    def __init__(self):
        # --- Cluster ---

        self.cluster: Optional[OpCompileConfig.ClusterConfig] = None

        # --- Compile Target ---

        self.framework: Optional[CompileFramework] = None
        self.language: Optional[CompileLanguage] = None
        self.computeMode: Optional[CompileComputeMode] = None
        self.parallelism: Optional[CompileParallelism] = None
        self.parallelismCount = 1

        self.manual = False

        self.enforceTupleOrder = True  # If tuples should always be processed in order of original occurrence

        # --- Desired Target Stats ---

        self.targetStats = OpCompileConfig.TargetStatsConfig()

    def setCluster(self, cluster: CompileCluster):
        self.cluster = OpCompileConfig.ClusterConfig(cluster.id)

    def setTarget(self, other: OpCompileConfig):
        self.framework = other.framework
        self.language = other.language
        self.computeMode = other.computeMode
        self.parallelism = other.parallelism
        self.parallelismCount = other.parallelismCount

    def setParallelism(self, paraCount: int):
        self.parallelismCount = paraCount
        self.parallelism = CompileParallelism.DISTRIBUTED if paraCount > 1 else CompileParallelism.SINGLE_NODE

    def reset(self):
        self.resetTarget()
        self.resetCluster()

    def resetTarget(self):
        self.framework = None
        self.language = None
        self.computeMode = None
        self.parallelism = None
        self.parallelismCount = 1
        self.manual = False

    def resetCluster(self):
        self.cluster = None

    def hasValidTarget(self):
        return (self.framework is not None
                and self.language is not None
                and self.computeMode is not None
                and self.parallelism is not None)

    def hasValidCluster(self):
        return self.cluster is not None

    @staticmethod
    def fromJSON(data) -> OpCompileConfig:
        cfg = OpCompileConfig()

        cfg.cluster = OpCompileConfig.ClusterConfig.fromJSON(data["cluster"])

        cfg.framework = CompileFramework.parse(data["framework"])
        cfg.language = CompileLanguage.parse(data["language"])
        cfg.computeMode = CompileComputeMode.parse(data["computeMode"])
        cfg.parallelism = CompileParallelism.parse(data["parallelism"])
        cfg.parallelismCount = tryParseInt(data["parallelismCount"], 1)

        if cfg.parallelism == CompileParallelism.SINGLE_NODE:
            cfg.parallelismCount = 1

        cfg.manual = data["manual"]

        cfg.enforceTupleOrder = data.get("enforceTupleOrder", cfg.enforceTupleOrder)

        cfg.targetStats = OpCompileConfig.TargetStatsConfig.fromJSON(data["targetStats"])

        return cfg

    def toJSON(self):
        return {"cluster": self.cluster.toJSON() if self.cluster is not None else None,
                "framework": self.framework.value,
                "language": self.language.value,
                "computeMode": self.computeMode.value,
                "parallelism": self.parallelism.value,
                "parallelismCount": self.parallelismCount,
                "enforceTupleOrder": self.enforceTupleOrder,
                "manual": self.manual,
                "targetStats": self.targetStats.toJSON()}

    class ClusterConfig:
        def __init__(self, clusterID: int):
            self.clusterID = clusterID
            self.clusterCons: Dict[int, OpCompileConfig.ClusterConnectionConfig] = dict()

        def toJSON(self) -> Dict:
            ccs = {}

            for con in self.clusterCons.values():
                ccs[con.conID] = con.toJSON()

            return {"id": self.clusterID, "ccs": ccs}

        @staticmethod
        def fromJSON(data: Dict) -> Optional[OpCompileConfig.ClusterConfig]:
            if data is None:
                return None

            clusterConf = OpCompileConfig.ClusterConfig(data["id"])

            for v in data["ccs"].values():
                ccData = OpCompileConfig.ClusterConnectionConfig.fromJSON(v)

                clusterConf.createConnectionConfig(ccData.conID, ccData.conType, ccData.params)

            return clusterConf

        def createConnectionConfig(self, conID: int, conType: CompileFrameworkConnector, params: Dict):
            self.clusterCons[conID] = OpCompileConfig.ClusterConnectionConfig(conID, conType, params)

        def removeConnectionConfig(self, conID: int):
            self.clusterCons.pop(conID, None)

        def getConnectionConfig(self, conID: int) -> Optional[OpCompileConfig.ClusterConnectionConfig]:
            return self.clusterCons.get(conID, None)

    class ClusterConnectionConfig:
        def __init__(self, conID: int, conType: CompileFrameworkConnector, params: Dict):
            self.conID = conID
            self.conType = conType
            self.params = params

        def toJSON(self) -> Dict:
            return {"conID": self.conID, "conType": self.conType.value, "params": escapeStrInDict(self.params, True)}

        @staticmethod
        def fromJSON(data: Dict) -> OpCompileConfig.ClusterConnectionConfig:
            return OpCompileConfig.ClusterConnectionConfig(data["conID"],
                                                           CompileFrameworkConnector.parse(data["conType"]),
                                                           escapeStrInDict(data["params"], False))

    class TargetStatsConfig:
        def __init__(self, autoTp: bool = True, targetTp: Optional[float] = None,
                     autoExTime: bool = True, targetExTime: Optional[float] = None,
                     exTimeSource: str = "None"):
            self.autoTp = autoTp
            self.targetTp = targetTp
            self.autoExTime = autoExTime
            self.targetExTime = targetExTime
            self.exTimeSource = exTimeSource  # Source of data, Read-Only

            # Internal vars | Calculated

            self.maxTargetTp: Optional[int] = targetTp  # Max achievable tp based on fastest input stream

        def toJSON(self):
            return {"autoTp": self.autoTp, "targetTp": round(self.targetTp, 2) if self.targetTp is not None else 0,
                    "autoExTime": self.autoExTime, "targetExTime": round(self.targetExTime * 1000, 2) if self.targetExTime is not None else 0,
                    "exTimeSource": self.exTimeSource}

        @staticmethod
        def fromJSON(data: Dict) -> OpCompileConfig.TargetStatsConfig:
            return OpCompileConfig.TargetStatsConfig(data["autoTp"], tryParseFloat(data["targetTp"], None),
                                                     data.get("autoExTime", True), tryParseFloat(data.get("targetExTime"), 0) / 1000)
