from typing import Optional, Callable, Dict

from spe.pipeline.pipeline import Pipeline
from spe.runtime.runtimeManager import RuntimeManager
from spe.runtime.simulation.simulator.interactive.interactivePipelineSim import InteractivePipelineSim
from spe.runtime.simulation.simulator.petriNet.petriNetPipelineSim import PetriNetPipelineSim
from spe.runtime.simulation.simulator.pipelineSimulator import PipelineSimulator, PipelineSimulationMode

# TODO: CURRENTLY, NO CLEAN UP AFTER STOPPING OF SIMULATION!


class PipelineSimulation:
    def __init__(self, pipeline: Pipeline, runtimeManager: RuntimeManager):
        self.pipeline = pipeline
        self.manager = runtimeManager

        self.simulator: Optional[PipelineSimulator] = None

    def start(self, duration: float, mode: PipelineSimulationMode, sourceCfgs: Dict, metaData: Dict, settingsCallback: Callable):
        if mode == PipelineSimulationMode.INTERACTIVE:
            self.simulator = InteractivePipelineSim(self.pipeline, self.manager)
            self.simulator.start(duration, sourceCfgs, metaData, settingsCallback)
        elif mode == PipelineSimulationMode.PETRINET:
            self.simulator = PetriNetPipelineSim(self.pipeline, self.manager)
            self.simulator.start(duration, sourceCfgs, metaData, settingsCallback)
