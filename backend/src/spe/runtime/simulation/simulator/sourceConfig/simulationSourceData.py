import json
import random
from _decimal import Decimal
from abc import ABC, abstractmethod
from typing import List, Tuple

import numpy as np

from spe.runtime.simulation.simulationDummyData import SimulationDummyData
from utils.utils import clamp


class SimulationSourceData(ABC):
    def __init__(self):
        ...

    @abstractmethod
    def getData(self) -> Tuple:
        pass

    @abstractmethod
    def getDataVariations(self) -> Tuple[List[Tuple[float, SimulationDummyData]], ...]:
        # For each output socket returns a list of possible values with chance
        pass


class NormalDistSSD(SimulationSourceData):
    def __init__(self, means: List[float], deviations: List[float]):
        super(NormalDistSSD, self).__init__()

        self.means = means
        self.deviations = deviations

    def getData(self) -> Tuple:
        return tuple([SimulationDummyData(np.random.normal(self.means[i], self.deviations[i]), 0) for i in range(len(self.means))])

    def getDataVariations(self) -> Tuple[List[Tuple[float, SimulationDummyData]], ...]:  # TODO: IMPROVE VARIATION FOR NORMAL DIST
        res = []

        for m in self.means:
            entries = [(1.0, SimulationDummyData(m, 0))]

            res.append(entries)

        return tuple(res)


class InvNormalDistSSD(SimulationSourceData):
    def __init__(self, means: List[float], deviations: List[float]):
        super(InvNormalDistSSD, self).__init__()

        self.means = means
        self.deviations = deviations

    def getData(self) -> Tuple:
        return tuple([SimulationDummyData(self.means[i] - np.random.normal(self.means[i], self.deviations[i]), 0) for i in range(len(self.means))])

    def getDataVariations(self) -> Tuple[List[Tuple[float, SimulationDummyData]], ...]:  # TODO: IMPROVE VARIATION FOR NORMAL DIST
        res = []

        for m in self.means:
            entries = [(1.0, SimulationDummyData(m, 0))]

            res.append(entries)

        return tuple(res)


class CustomSSD(SimulationSourceData):
    def __init__(self, customData: str):
        super(CustomSSD, self).__init__()

        self.sockets = []

        for socketData in customData:
            socketVariations = []
            remainingChance = Decimal(1.0)

            split = socketData.split(",")

            for sID in range(len(split)):
                s = split[sID]

                sData = s.split(";")

                data = json.loads(sData[0]) if len(sData[0].strip()) > 0 else None
                chance = clamp(Decimal(sData[1]) if len(sData) == 2 else 1, 0, remainingChance)

                remainingChance -= chance

                # For last entry set all the remaining chance
                if sID == len(split) - 1:
                    remainingChance = Decimal(0.0)

                socketVariations.append((data, remainingChance))

            self.sockets.append(socketVariations)

    def getData(self) -> Tuple:
        data = []

        for socket in self.sockets:
            r = random.random()

            for v in socket:
                if r >= v[1]:
                    data.append(SimulationDummyData(v[0], 0))

                    break

        return tuple(data)

    def getDataVariations(self) -> Tuple[List[Tuple[float, SimulationDummyData]], ...]:
        res = []

        for socket in self.sockets:
            entries = []

            remainingChance = Decimal(1.0)
            totalChance = Decimal(0.0)

            for vID in range(len(socket)):
                v = socket[vID]

                remainingChance: Decimal = clamp(remainingChance - v[1], 0.0, 1.0)

                # Set remaining chance for last element
                if vID == len(socket) - 1:
                    remainingChance = 1 - totalChance

                totalChance: Decimal = clamp(totalChance + remainingChance, 0.0, 1.0)

                entries.append((float(remainingChance), SimulationDummyData(v[0], 0)))

            res.append(entries)

        return tuple(res)
