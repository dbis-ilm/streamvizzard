import json
from enum import Enum
from typing import Optional, List

from analysis.costModel.configurations.costModelOpSetups import OpInputDataFeature
from analysis.costModel.costModel import CostModel, CostModelTarget
from spe.pipeline.operators.source import Source
from spe.runtime.simulation.simulator.sourceConfig.simulationSourceData import SimulationSourceData, NormalDistSSD, \
    InvNormalDistSSD, CustomSSD


class PipelineSourceDataMode(Enum):
    NORMAL_DIST = "normalDist"
    NORMAL_DIST_INV = "normalDistInv"
    CUSTOM = "custom"

    @staticmethod
    def parse(sm: str):
        for v in PipelineSourceDataMode:
            if v.value == sm:
                return v

        return None


class SimulationSourceConfig:
    def __init__(self, mode: PipelineSourceDataMode, rate: float, data: SimulationSourceData):
        self.mode = mode
        self.data = data
        self.rate = rate  # The rate in seconds, e.g: 0.25 = 4 elements per second

    @staticmethod
    def createConfig(s: Source, sourceConfigs: json, costModelPath: str):
        dataMode = PipelineSourceDataMode.NORMAL_DIST
        rate = 0
        data: Optional[SimulationSourceData] = None
        custom = ""

        for scfg in sourceConfigs:
            if scfg["id"] == s.id:
                dataMode = PipelineSourceDataMode.parse(scfg["data"])
                rate = 1.0 / scfg["rate"] if scfg["rate"] != 0 else 0
                custom = scfg["custom"]

                break

        if dataMode == PipelineSourceDataMode.NORMAL_DIST or \
                dataMode == PipelineSourceDataMode.NORMAL_DIST_INV:

            outFeats: List[Optional[OpInputDataFeature]] = []

            # Try to find IN features of child operators (coming from this source) to get produced values of this source

            for outP in s.outputs:
                cons = outP.getConnections()

                outFeats.append(None)

                if len(cons) > 0:
                    con = cons[0]
                    op = con.input.op

                    model = CostModel.load(type(op), costModelPath)

                    if model is not None:
                        exTime = model.getVariant(CostModelEnv.SV_CPU, CostModelTarget.EXECUTION_TIME)

                        if exTime is not None:
                            for feat in exTime.features:
                                if isinstance(feat, OpInputDataFeature) and feat.socketID == con.input.id:
                                    outFeats[feat.socketID] = feat

                                    break

            means = [feat.stats.avg if feat is not None else 0 for feat in outFeats]
            deviations = [feat.stats.std if feat is not None else 0 for feat in outFeats]

            data = NormalDistSSD(means, deviations) if dataMode == PipelineSourceDataMode.NORMAL_DIST \
                else InvNormalDistSSD(means, deviations)
        elif dataMode == PipelineSourceDataMode.CUSTOM:
            data = CustomSSD(custom)

        return SimulationSourceConfig(dataMode, rate, data)
