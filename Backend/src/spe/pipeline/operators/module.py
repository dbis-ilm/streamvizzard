from __future__ import annotations
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
    def isArrayOf(x, arrayType, allowNone: bool = False):
        if isinstance(x, list):
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
        self.operators: Dict[str, Operator] = dict()
        self.pathLookup: Dict[Type[Operator], str] = dict()
        self.monitorDataTypes: List[MonitorDataType] = list()
        self.advisorStrategies: Dict[Union[Any, Type[Operator]], List[Type[AdvisorStrategy]]] = dict()
        self._jsonEncoders: Dict[type, Callable] = dict()

    @abstractmethod
    def initialize(self):
        pass

    def getOperator(self, name: str) -> Operator:
        return self.operators.get(name, None)

    def getOperatorPath(self, operator: Type[Operator]):
        return self.pathLookup.get(operator, None)

    def registerOp(self, op, path):
        self.operators[path] = op
        self.pathLookup[op] = path

    def registerMonitorDataType(self, dtype: MonitorDataType):
        self.monitorDataTypes.append(dtype)

    def registerJSONEncoder(self, dtype: type, encoder: Callable):
        self._jsonEncoders[dtype] = encoder

    def registerAdvisorStrategy(self, operators: Union[List[Type[Operator]], Any], strategy: Type[AdvisorStrategy]):
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

    def getJSONEncoder(self, dtype: type):
        return self._jsonEncoders.get(dtype, None)

    def getAdvisorStrategies(self, operator: Operator) -> Optional[List[Type[AdvisorStrategy]]]:
        opRes = self.advisorStrategies.get(type(operator))
        allRes = self.advisorStrategies.get(Any)

        if opRes is not None and allRes is not None:
            return opRes + allRes
        elif opRes is not None:
            return opRes
        elif allRes is not None:
            return allRes

        return None
