from __future__ import annotations

import importlib
from typing import TYPE_CHECKING
import logging
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Type, Any, Union

from spe.common.dataType import DataType
from spe.runtime.monitor.dataInspectType import DataInspectType
from spe.runtime.monitor.dataDisplayType import DataDisplayType

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.advisor.advisorStrategy import AdvisorStrategy


class Module(ABC):
    def __init__(self, name: str):
        self.name = name
        self.operators: Dict[str, tuple[str, str]] = dict()
        self.pathLookup: Dict[str, str] = dict()

        self.monitorDataTypes: List[DataDisplayType] = list()
        self.monitorInspectTypes: List[DataInspectType] = list()

        self.advisorStrategies: Dict[Union[Any, str], List[Type[AdvisorStrategy]]] = dict()

    @abstractmethod
    def initialize(self):
        pass

    def getOperator(self, name: str) -> Optional[Operator]:
        path = self.operators.get(name, None)

        if path is None:
            return None

        try:
            module = importlib.import_module(path[0])
            class_ = getattr(module, path[1])

            return class_
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return None

    def getOperatorPath(self, operator: Type[Operator]):
        return self.pathLookup.get(operator.__module__ + "." + operator.__name__, None)

    def registerOp(self, modulePath: str, opName: str, path: str):
        self.operators[path] = (modulePath, opName)
        self.pathLookup[modulePath + "." + opName] = path

    def registerMonitorDataType(self, dtype: DataDisplayType):
        if isinstance(dtype, DataInspectType):
            self.monitorInspectTypes.append(dtype)
        else:
            self.monitorDataTypes.append(dtype)

    def registerAdvisorStrategy(self, operators: List[str] | Any, strategy: Type[AdvisorStrategy]):
        if operators is not Any:  # Register for specific operators
            for operator in operators:
                if operator in self.advisorStrategies:
                    self.advisorStrategies[operator].append(strategy)
                else:
                    self.advisorStrategies[operator] = [strategy]
        else:  # Register for all operators
            if Any in self.advisorStrategies:
                self.advisorStrategies[Any].append(strategy)
            else:
                self.advisorStrategies[Any] = [strategy]

    def getMonitorDataType(self, dataType: DataType) -> Optional[DataDisplayType]:
        for k in self.monitorDataTypes:
            if k.supportsType(dataType):
                return k

        return None

    def getMonitorInspectType(self, dataType: DataType) -> Optional[DataInspectType]:
        for k in self.monitorInspectTypes:
            if k.supportsType(dataType):
                return k

        return None

    def getAdvisorStrategies(self, operator: Operator) -> Optional[List[Type[AdvisorStrategy]]]:
        opRes = self.advisorStrategies.get(operator.__module__ + "." + operator.__class__.__name__)
        allRes = self.advisorStrategies.get(Any)

        if opRes is not None and allRes is not None:
            return opRes + allRes
        elif opRes is not None:
            return opRes
        elif allRes is not None:
            return allRes

        return None
