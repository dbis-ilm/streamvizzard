from __future__ import annotations
import os
import sys
import time
from typing import List, TYPE_CHECKING

from config import Config
from analysis.costModel.calculator.costModelCalculator import CostModelCalculator, CostModelVisualization
from analysis.costModel.configurations.imageProcessingConf import ImageProcessingConf
from analysis.costModel.configurations.dataCleaningConf import DataCleaningConf

from analysis.costModel.operatorEntry import OperatorEntry
from streamVizzard import StreamVizzard

if TYPE_CHECKING:
    from analysis.costModel.configurations.costModelOpSetups import CostModelOpCfg


class CostModelAnalysis:
    """
    Management class for calculating operator costModels based on predefined configurations.
    """

    def __init__(self):
        self._operatorEntries: List[OperatorEntry] = list()

    def execute(self, visBestModel: CostModelVisualization, storagePath: str,
                saveModels: bool = True, forceRecordings: bool = False,
                printIntermediateResults: bool = False):

        # Setup folders

        recordingsPath = os.path.join(storagePath, "Recordings")
        modelPath = os.path.join(storagePath, "Models")

        os.makedirs(recordingsPath, exist_ok=True)
        os.makedirs(modelPath, exist_ok=True)

        print("Starting CostModelAnalysis!")

        cmc = CostModelCalculator()

        for opEntry in self._operatorEntries:
            print("\nExecuting: " + str(opEntry.opCfg.operator.getName()) + " ...")

            start = time.time()

            opEntry.collectRecordings(recordingsPath, forceRecordings)

            print(f"Gathering recordings took {round(time.time() - start, 2)}s\n")

            bm = cmc.calculateBestModel(opEntry, visBestModel, printIntermediateResults)

            if bm is not None and saveModels:
                bm.save(type(opEntry.opCfg.operator), modelPath)

        print("\nCostModelAnalysis completed!")

    def registerOperator(self, opCfg: CostModelOpCfg):
        self._operatorEntries.append(OperatorEntry(opCfg))


def performCostModelAnalysis(storagePath: str, forceRecordings: bool = False):
    _ = StreamVizzard(Config.getRuntimeOnly())  # Instance required for accessing config, but no need to start

    costModelAnalysis = CostModelAnalysis()

    # Register operator configs

    ImageProcessingConf(True, True, True, True, True, True, True).registerRuns(costModelAnalysis)
    DataCleaningConf(True, True, True).registerRuns(costModelAnalysis)

    # Execute

    costModelAnalysis.execute(visBestModel=CostModelVisualization.NONE, storagePath=storagePath,
                              forceRecordings=forceRecordings, printIntermediateResults=False)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("Storage path arg required!")

    performCostModelAnalysis(sys.argv[1], False)
