from typing import Dict, Optional, Callable

from analysis.costModel.costModel import CostModelVariant, CostModel, CostModelTarget, CostModelEnv, CostModelMetaData
from spe.pipeline.operators.base.dataTypes.window import Window
from spe.pipeline.operators.base.operators.windows.tumblingWindowCount import TumblingWindowCount
from spe.pipeline.operators.operator import Operator
from spe.pipeline.operators.source import Source
from spe.pipeline.pipeline import Pipeline
from spe.pipeline.pipelineUpdates import PipelineUpdate
from spe.runtime.runtimeManager import RuntimeManager
from spe.runtime.simulation.simulationDummyData import SimulationDummyData
from spe.runtime.simulation.simulationTick import SimulationTick
from spe.runtime.simulation.simulator.pipelineSimulator import PipelineSimulator, PipelineSimulationMode
from spe.runtime.simulation.simulator.sourceConfig.simulationSourceConfig import SimulationSourceConfig
from spe.common.tuple import Tuple


class InteractivePipelineSim(PipelineSimulator):
    def __init__(self, pipeline: Pipeline, runtimeManager: RuntimeManager):
        super(InteractivePipelineSim, self).__init__(pipeline, runtimeManager, PipelineSimulationMode.INTERACTIVE)

        self._opModels: Dict[int, CostModel] = dict()
        self._opModelVariants: Dict[Operator, Dict[CostModelTarget, CostModelVariant]] = dict()

        self._sourceConfigs = []
        self._costModelFolder = ""

    def start(self, duration: float, sourceCfgs: Dict, metaData: Dict, settingsCallback: Optional[Callable]):
        self._costModelFolder = metaData["costModelPath"]

        self._sourceConfigs = sourceCfgs

        self.pipeline.registerEvent(Pipeline.EVENT_PIPELINE_UPDATED, self._onPipelineUpdated)

        self._onPipelineUpdated()

        self._startSimulation(duration, settingsCallback)

    def _onPipelineUpdated(self, pu: Optional[PipelineUpdate] = None):
        if pu is not None and not pu.isLogicalChange():  # Meta / ui data updates
            return

        self._loadCostModels()
        self._prepareOperators()
        self._prepareSources()

    def _loadCostModels(self):
        for op in self.pipeline.getAllOperators():
            if op in self._opModelVariants:  # Already loaded
                continue

            cm = CostModel.load(type(op), self._costModelFolder)

            if cm is None:
                continue

            modelVariants = dict()
            modelVariants[CostModelTarget.EXECUTION_TIME] = cm.getVariant(CostModelEnv.SV_CPU, CostModelTarget.EXECUTION_TIME)
            modelVariants[CostModelTarget.OUTPUT_SIZE] = cm.getVariant(CostModelEnv.SV_CPU, CostModelTarget.OUTPUT_SIZE)

            self._opModelVariants[op] = modelVariants
            self._opModels[op.id] = cm

    def _startSimulation(self, duration: float, settingsCallback: Optional[Callable]):
        # Start pipeline to be able to modify debugging history

        if not self.manager.startPipeline(self.pipeline, settingsCallback):
            return  # TODO: Check for error

        self._simulationTick = SimulationTick(duration)

        self._simulationTick.start(self.manager.getEventLoop())

    def _prepareSources(self):
        instance = self

        def exFunc(source: Source, config: SimulationSourceConfig):
            while not instance._simulationTick.isCompleted():
                instance._simulationTick.waitDuration(config.rate)

                if not source.isRunning():
                    break

                producedTuple = config.data.getData()

                source._produce(producedTuple)

        for s in self.pipeline.getSources():
            sCfg = SimulationSourceConfig.createConfig(s, self._sourceConfigs, self._costModelFolder)

            s._runSource = lambda source=s, cfg=sCfg: exFunc(source, cfg)

    def _prepareOperators(self):
        instance = self

        def exOp(operator: Operator, tup: Tuple):
            if instance._simulationTick.isCompleted():
                return None

            opModel = instance._opModels.get(operator.id, None)
            exTime = instance._getOperatorPrediction(operator, tup, CostModelTarget.EXECUTION_TIME) / 1000
            dataSize = instance._getOperatorPrediction(operator, tup, CostModelTarget.OUTPUT_SIZE)

            instance._simulationTick.waitDuration(exTime)

            # TODO: Review (removed from costmodel -> too pipeline-specific)
            # dataTransformFunc = opModel.dataTransform if opModel is not None else None
            dataTransformFunc = None

            if dataTransformFunc is not None:
                resData = dataTransformFunc([td.inputData if td is not None else None for td in tup.data], operator)

                if resData is not None:
                    resData = tuple([SimulationDummyData(d, dataSize) for d in resData])
            else:
                resData = tup.data

            if resData is None:
                return None

            return operator.createTuple(resData)

        def exTumblingCountWindow(tup: Tuple, origFunc: Callable):
            res: Tuple = origFunc(tup)

            if res is None:
                return None

            window: Window = res.data[0]

            simData = SimulationDummyData(window.getCount() * window.getDataAt(0).inputData, window.getCount() * window.getDataAt(0).dataSize)
            simData.getTuples = lambda: window.getTuples()  # Add function to sim object to enable undo/redo of window op

            res.data = (simData,)

            return res

        for op in self.pipeline.getAllOperators():
            # Here we should handle operators that need special treatment like windows
            if isinstance(op, TumblingWindowCount):
                op._execute = lambda t, origFunc=op._execute: exTumblingCountWindow(t, origFunc)
            else:
                op._onExecutionUndo = lambda tup: None
                op._onExecutionRedo = lambda tup: None

                if not op.isSource():
                    op._execute = lambda t, operator=op: exOp(operator, t)

    def _getOperatorPrediction(self, operator: Operator, tup: Tuple, target: CostModelTarget):
        model = self._opModelVariants.get(operator)

        if model is None:
            return 0

        variant = model.get(target)

        if variant is None:
            return 0

        totalDataSize = 0

        for d in tup.data:
            totalDataSize += d.dataSize

        return variant.predict(operator, tup.data, CostModelMetaData.construct(totalDataSize)) * 1000  # s -> ms
