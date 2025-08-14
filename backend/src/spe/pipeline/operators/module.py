from __future__ import annotations

import importlib
from typing import TYPE_CHECKING
import logging
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Callable, Optional, List, Type, Any, Union

from spe.pipeline.operators.base.dataTypes.window import Window

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.advisor.advisorStrategy import AdvisorStrategy
    from spe.runtime.monitor.dataInspect import DataInspect


class MonitorDataType:
    def __init__(self, name: str, checkFunc: Callable):
        self._name = name
        self._checkFunc = checkFunc

        # If this is not None the data will be transformed into another type instead of preparing for display
        self._transformFunc: Optional[Callable] = None

        # If this is not None the data will be available for inspect
        self._dataInspect: Optional[Type[DataInspect]] = None

        self._displayModes: Dict[int, Callable] = dict()

    def isDataType(self, data) -> bool:
        return self._checkFunc(data)

    def isTransformType(self) -> bool:
        return self._transformFunc is not None

    def isInspectType(self) -> bool:
        return self._dataInspect is not None

    def registerTransformFunc(self, func: Callable):
        self._transformFunc = func

    def registerDisplayMode(self, mode: int, func: Callable):
        # Make sure that the func does not modify the original input data! Create a copy if required
        self._displayModes[mode] = func

    def registerInspect(self, inspect: Type[DataInspect]):
        self._dataInspect = inspect

    def getName(self) -> str:
        return self._name

    def getInspectInstance(self) -> DataInspect:
        return self._dataInspect()

    def transform(self, data):
        if self._transformFunc is None:
            return data

        return self._transformFunc(data)

    def hasDisplayMode(self, dMode: int) -> bool:
        prep = self._displayModes.get(dMode, None)

        return prep is not None

    def prepareForDisplayMode(self, dMode: int, data, settings):
        prep = self._displayModes.get(dMode, None)

        if prep is None:
            return data

        try:
            if settings is None:
                settings = {}

            return prep(data, settings)
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return None

    # Static helpers

    @staticmethod
    def isArrayOf(x, arrayType, allowNone: bool = False, allowEmpty: bool = False):
        if isinstance(x, list):
            if len(x) == 0:
                return allowEmpty

            for d in x:
                if isinstance(d, arrayType):
                    return True
                elif d is None and allowNone:
                    continue
                else:
                    return False

        return False

    @staticmethod
    def isWindowOf(x, dataType):
        return isinstance(x, Window) and x.isTypeOf(dataType)


class Module(ABC):
    def __init__(self, name: str):
        self.name = name
        self.operators: Dict[str, tuple[str, str]] = dict()
        self.pathLookup: Dict[str, str] = dict()
        self.monitorDataTypes: List[MonitorDataType] = list()
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

    def registerMonitorDataType(self, dtype: MonitorDataType):
        self.monitorDataTypes.append(dtype)

    def registerAdvisorStrategy(self, operators: Union[List[str], Any], strategy: Type[AdvisorStrategy]):
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

    def getMonitorDataType(self, data) -> Optional[MonitorDataType]:
        for k in self.monitorDataTypes:
            if k.isDataType(data):
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
