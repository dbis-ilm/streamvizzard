from __future__ import annotations
import random
from typing import Tuple, TYPE_CHECKING

from analysis.costModel.configurations.costModelOpSetups import CostModelOpSetups, CostModelOpCfg, \
    OpParamFeature, OpMetaDataFeature
from analysis.costModel.costModel import CostModelEnv, CostModelTarget, CostModelMetaData
from analysis.costModel.executionRecording import RecordingParam

if TYPE_CHECKING:
    from analysis.costModel.costModelAnalysis import CostModelAnalysis


class DataCleaningConf(CostModelOpSetups):
    def __init__(self, runMissingVal: bool = True, runAnomaly: bool = True, runInconsistency: bool = True):
        super(DataCleaningConf, self).__init__()

        self._runMissingVal = runMissingVal
        self._runAnomaly = runAnomaly
        self._runInconsistency = runInconsistency

        self._its = 50_000
        self._repetition = 10

    def registerRuns(self, cma: CostModelAnalysis):
        if self._runAnomaly:
            from spe.pipeline.operators.dataCleaning.operators.anomalyDetection import AnomalyDetection

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(AnomalyDetection),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateData(False, 25, 150),
                                   lambda runID: {"mode": random.choice(["mean", "mode", "median", "remove"]),
                                                  "upperQuantile": random.randint(70, 80),
                                                  "lowerQuantile": random.randint(20, 30),
                                                  "windowSize": random.randint(20, 30)},
                                   lambda tup, op: [RecordingParam("mode", op.mode),
                                                    RecordingParam("upperQuantile", op.upperQuantile),
                                                    RecordingParam("lowerQuantile", op.lowerQuantile),
                                                    RecordingParam("windowSize", op.windowSize),
                                                    RecordingParam("inputLength", len(tup[0]))],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpMetaDataFeature(CostModelMetaData.Param.INPUT_DATA_SIZE),
                                               OpParamFeature("mode",
                                                              lambda res: ["mean", "mode", "median", "remove"].index(res.getValue("mode")) + 1,
                                                              lambda op: ["mean", "mode", "median", "remove"].index(op.mode) + 1),
                                               OpParamFeature("upperQuantile",
                                                              lambda res: res.getValue("upperQuantile"),
                                                              lambda op: op.upperQuantile),
                                               OpParamFeature("lowerQuantile",
                                                              lambda res: res.getValue("lowerQuantile"),
                                                              lambda op: op.lowerQuantile),
                                               OpParamFeature("windowSize",
                                                              lambda res: res.getValue("windowSize"),
                                                              lambda op: op.windowSize)
                                               ],
                                   )
                               ]))

        if self._runMissingVal:
            from spe.pipeline.operators.dataCleaning.operators.missingValues import MissingValues

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(MissingValues),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateData(True, 25, 150),
                                   lambda runID: {"mode": random.choice(["linear", "polynomial", "padding", "drop"])},
                                   lambda tup, op: [RecordingParam("mode", op.mode),
                                                    RecordingParam("inputLength", len(tup[0]))],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpMetaDataFeature(CostModelMetaData.Param.INPUT_DATA_SIZE),
                                               OpParamFeature("mode",
                                                              lambda res: ["linear", "polynomial", "padding", "drop"].index(res.getValue("mode")) + 1,
                                                              lambda op: ["linear", "polynomial", "padding", "drop"].index(op.mode) + 1)],
                                   )
                               ]))

        if self._runInconsistency:
            from spe.pipeline.operators.dataCleaning.operators.inconsistencies import Inconsistency

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(Inconsistency),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateData(False, 25, 150),
                                   lambda runID: {"mode": random.choice(["mean", "median"]),
                                                  "threshold": random.uniform(0, 2),
                                                  "maxValue": random.uniform(1.5, 10)},
                                   lambda tup, op: [RecordingParam("mode", op.mode),
                                                    RecordingParam("threshold", op.threshold),
                                                    RecordingParam("maxValue", op.maxValue),
                                                    RecordingParam("inputLength", len(tup[0]))],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpMetaDataFeature(CostModelMetaData.Param.INPUT_DATA_SIZE)],
                                   )
                               ]))

    @staticmethod
    def _generateData(includeMissing: bool, minLength: int, maxLength: int) -> Tuple:
        dataLength = random.randint(minLength, maxLength)
        outlierChance = random.uniform(0.125, 0.175)
        missingChance = random.uniform(0.125, 0.175)

        res = []

        for i in range(dataLength):
            if includeMissing and random.random() <= missingChance:
                val = None
            else:
                val = random.uniform(0.5, 1.5)

                if random.random() <= outlierChance:
                    val *= 100

            res.append(val)

        return res,
