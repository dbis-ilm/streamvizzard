from __future__ import annotations
from typing import TYPE_CHECKING

import string
from typing import Dict, Callable, Optional, List, Type

import config


if TYPE_CHECKING:
    from spe.pipeline.operators.module import Module, MonitorDataType
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.advisor.advisorStrategy import AdvisorStrategy

__modules: Dict[str, Module] = dict()


def __registerModule(module: type(Module)):
    mod = module()
    __modules[mod.name] = mod

    mod.initialize()


def getOperatorByPath(path: string) -> Optional[Operator]:
    opPathComps = path.split("/")

    opMod = opPathComps[0]
    opIdentifier = ""

    for i in range(1, len(opPathComps)):
        if i > 1:
            opIdentifier += '/' + opPathComps[i]
        else:
            opIdentifier += opPathComps[i]

    module = __modules.get(opMod)

    if module is None:
        return None

    return module.getOperator(opIdentifier)


def getPathByOperator(operator: Type[Operator]) -> Optional[str]:
    for module in __modules.values():
        path = module.getOperatorPath(operator)

        if path is not None:
            return module.name + "/" + path

    return None


def getJSONEncoderForDataType(data) -> Optional[Callable]:
    for module in __modules.values():
        encoder = module.getJSONEncoder(type(data))

        if encoder is not None:
            return encoder

    return None


def getDisplayDataType(data) -> Optional[MonitorDataType]:
    for module in __modules.values():
        displayType = module.getMonitorDataType(data)

        if displayType is not None:
            return displayType

    return None


def getAdvisorStrategies(operator: Operator) -> Optional[List[AdvisorStrategy]]:
    res = []

    for module in __modules.values():
        strategies = module.getAdvisorStrategies(operator)

        if strategies is None:
            continue

        for s in strategies:
            res.append(s(operator))

    if len(res) == 0:
        return None

    return res


# ------------- MODULE REGISTRATION -------------


def _registerBase():
    from spe.pipeline.operators.base.baseModule import BaseModule

    __registerModule(BaseModule)


def _registerImageProc():
    from spe.pipeline.operators.imageProc.imageProcModule import ImageProcModule

    __registerModule(ImageProcModule)


_registerBase()
_registerImageProc() if config.MODULE_USE_IMAGE_PROCESSING else None
