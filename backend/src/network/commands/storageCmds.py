from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Dict

from network.commands.commands import Command
from spe.common.configStorage import ConfigStorage

if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager


class RetrieveStoredPipelines(Command):
    def __init__(self):
        super().__init__("listStoredPipelines")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional[str]:
        pipelines = ConfigStorage.listStoredPipelines()

        return json.dumps(pipelines)


class RequestStoredPipeline(Command):
    def __init__(self):
        super().__init__("requestStoredPipeline")

    def handleCommand(self, rm: RuntimeManager, data) -> Optional[str]:
        pipeline = ConfigStorage.loadStoredPipeline(data)

        return json.dumps(pipeline)


class DeleteStoredPipeline(Command):
    def __init__(self):
        super().__init__("deleteStoredPipeline")

    def handleCommand(self, rm: RuntimeManager, data) -> Optional[str]:
        removed = ConfigStorage.deleteStoredPipeline(data)

        return json.dumps(removed)


class StorePipeline(Command):
    def __init__(self):
        super().__init__("storePipeline")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional[str]:
        stored = ConfigStorage.storePipeline(data["name"], data["data"])

        return json.dumps(stored)


class RetrieveStoredOperators(Command):
    def __init__(self):
        super().__init__("listStoredOperators")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional[str]:
        ops = ConfigStorage.listStoredOperators()

        return json.dumps(ops)


class DeleteStoredOperator(Command):
    def __init__(self):
        super().__init__("deleteStoredOperator")

    def handleCommand(self, rm: RuntimeManager, data) -> Optional[str]:
        removed = ConfigStorage.deleteStoredOperator(data)

        return json.dumps(removed)


class StoreOperator(Command):
    def __init__(self):
        super().__init__("storeOperator")

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> Optional[str]:
        stored = ConfigStorage.storeOperator(data)

        return json.dumps(stored)
