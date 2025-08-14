from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager


class Command(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def handleCommand(self, rm: RuntimeManager, data) -> Optional:
        ...
