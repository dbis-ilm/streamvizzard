from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from utils.svResult import SvResult

if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from network.server import NetworkMode


class Command(ABC):
    def __init__(self, name: str, networkMode: NetworkMode):
        self.name = name
        self.networkMode = networkMode

    @abstractmethod
    def handleCommand(self, rm: RuntimeManager, data) -> CommandRes:
        ...


class CommandRes(SvResult):
    def __init__(self, resData: Optional[str] = None, error: Optional[str] = None):
        super().__init__(error)

        self.resData = resData

    @staticmethod
    def ok():
        return CommandRes()

    @staticmethod
    def error(msg: Optional[str] = None):
        return CommandRes(error=json.dumps({"error": msg}))

    @staticmethod
    def okWithRes(resData: str) -> CommandRes:
        return CommandRes(resData)
