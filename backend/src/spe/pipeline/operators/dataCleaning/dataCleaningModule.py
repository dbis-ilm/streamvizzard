from typing import Any

from spe.pipeline.operators.dataCleaning.advisorStrategies.anomalyValueStrategy import AnomalyValueStrategy
from spe.pipeline.operators.dataCleaning.advisorStrategies.inconsistentValueStrategy import InconsistentValueStrategy
from spe.pipeline.operators.dataCleaning.advisorStrategies.missingValueStrategy import MissingValueStrategy
from spe.pipeline.operators.module import Module


class DataCleaningModule(Module):
    def __init__(self):
        super(DataCleaningModule, self).__init__("DataCleaning")

    def initialize(self):
        self.registerOp("spe.pipeline.operators.dataCleaning.operators.anomalyDetection", "AnomalyDetection", "Operators/AnomalyDetection")
        self.registerOp("spe.pipeline.operators.dataCleaning.operators.missingValues", "MissingValues", "Operators/MissingValues")
        self.registerOp("spe.pipeline.operators.dataCleaning.operators.inconsistencies", "Inconsistency", "Operators/Inconsistencies")

        # ------ Advisor Strategies ------
        self.registerAdvisorStrategy(Any, MissingValueStrategy)
        self.registerAdvisorStrategy(Any, InconsistentValueStrategy)
        self.registerAdvisorStrategy(Any, AnomalyValueStrategy)
