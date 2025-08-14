from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type, List, Callable, Any, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from analysis.costModel.costModel import CostModelTarget, CostModelEnv, CostModelMetaData
    from analysis.costModel.executionRecording import ExecutionRecording, RecordingParam


class CostModelOpSetups(ABC):
    @abstractmethod
    def registerRuns(self, cma):
        pass

    @staticmethod
    def _createOperator(t: Type[Operator]) -> Operator:
        op: Operator = t(0)

        return op


class CostModelOpCfg:
    """
    Configuration for the calculation of cost models for a specific operator.\n
    An operator costmodel can contain multiple variants for specific CodeModelTargets and CostModelEnvs.\n
    In general, the more features are set with high variations, the more data points/iterations are required for reliable results!\n
    Current limitation: Entries are identified by the operator class -> different UDFs with custom code are currently not supported\n
    Current limitation: Only numeric feature params are supported [workaround: internally map to int value -> care with 0!]\n
    """

    class TargetConfig:
        """ Target for the calculation of an operator cost model variant for the defined CostModelTarget and CostModelEnv. """

        def __init__(self, env: CostModelEnv, target: CostModelTarget, inputs: List[CostModelFeature]):
            self.env = env
            self.target = target
            self.inputs = inputs

        def retrieveInputParams(self, res: ExecutionRecording.Entry) -> List:
            return [i.recordRetriever(res) for i in self.inputs]

    class OpExecutionCfg:
        """ Configuration for executing the defined operator on the StreamVizzard system in order
        to recoder data points for the subsequent costModel calculation."""

        def __init__(self, dataLoader: Callable[[int], tuple],
                     dataRetriever: Optional[Callable[[int], Dict]],
                     paramRetriever: Callable[[tuple, Operator], List[RecordingParam]],
                     iterations: int, warmUp: int, repetitions: int,
                     postExecution: Optional[Callable] = None):
            self.dataRetriever = dataRetriever
            self.paramRetriever = paramRetriever
            self.dataLoader = dataLoader

            self.postExecution = postExecution

            self.iterations = iterations  # How many operator executions are performed
            self.warmUp = warmUp  # How many runs to skip for warmup before recording data
            self.repetitions = repetitions  # How many times one op execution is repeated (averaged runtime)

    def __init__(self, operator: Operator, runCfg: Optional[OpExecutionCfg],
                 targets: List[TargetConfig]):

        self.operator = operator

        self.runCfg = runCfg

        self.targets = targets


class CostModelFeatureStats:
    def __init__(self, minVal, maxVal, avgVal, median, std):
        self.min = minVal
        self.max = maxVal
        self.avg = avgVal
        self.median = median
        self.std = std


class CostModelFeature(ABC):
    """ All callables are stored inside the costModel using dill and must be serializable! """

    def __init__(self, name: str, recordRetriever: Callable[[ExecutionRecording.Entry], Any]):
        self.name = name
        self.recordRetriever = recordRetriever  # Retrieves the value from a stored recording entry

        self.stats: Optional[CostModelFeatureStats] = None  # Stats, describing the trained input data, calculated during model construction


class OpParamFeature(CostModelFeature):
    """ Feature based on specific operator parameters that are extracted directly from the operator. """

    def __init__(self, name: str, recordRetriever: Callable[[ExecutionRecording.Entry], Any], retriever: Callable[[Operator], Any]):
        super(OpParamFeature, self).__init__(name, recordRetriever)

        self.retriever = retriever  # Retrieves the value from an operator instance


class OpInputDataFeature(CostModelFeature):
    """ Feature based on input data of an operator that are extracted directly from the input data tuple. """

    def __init__(self, name: str, socketID: int, recordRetriever: Callable[[ExecutionRecording.Entry], Any], retriever: Callable[[tuple], Any]):
        super(OpInputDataFeature, self).__init__(name, recordRetriever)

        self.socketID = socketID
        self.retriever = retriever  # Retrieves the value from an input data tuple


class OpMetaDataFeature(CostModelFeature):
    """ Feature based on meta-data provided during the model prediction. """

    def __init__(self, metaParam: CostModelMetaData.Param):
        super(OpMetaDataFeature, self).__init__(metaParam.value, lambda res: res.getValue(metaParam.value))

        self.metaParam = metaParam
        self.retriever = lambda metaData: metaData.get(metaParam)  # Automatically retrieves the value from the cost model meta-data
