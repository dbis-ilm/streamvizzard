import time
from abc import ABC
from enum import Enum
from typing import Optional, Callable

from spe.pipeline.pipeline import Pipeline
from spe.runtime.runtimeManager import RuntimeManager
from spe.runtime.simulation.simulationTick import SimulationTick


class PipelineSimulationMode(Enum):
    INTERACTIVE = "interactive"
    PETRINET = "petriNet"

    @staticmethod
    def parse(sm: str):
        for v in PipelineSimulationMode:
            if v.value == sm:
                return v

        return None


class PipelineSimulator(ABC):
    def __init__(self, pipeline: Pipeline, runtimeManager: RuntimeManager, mode: PipelineSimulationMode):
        self.pipeline = pipeline
        self.manager = runtimeManager

        self._simulationTick: Optional[SimulationTick] = None
        self._executionMode = mode

    def _startSimulation(self, duration: float, settingsCallback: Optional[Callable]):
        # Start pipeline to be able to modify debugging history

        self.manager.startPipeline(self.pipeline, settingsCallback)

        self._simulationTick = SimulationTick(duration)

        # Wait for max 2 seconds, until pipeline is running

        startTime = time.time()

        while time.time() - startTime < 2:
            if self.manager.isRunning():
                self._simulationTick.start(self.manager.getEventLoop())
                break

    def _onError(self):
        if self.manager.isRunning():
            self.manager.stopPipeline()
