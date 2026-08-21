from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict

from network.commands.commands import Command, CommandRes
from spe.common.configStorage import ConfigStorage

if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from network.server import NetworkMode


class RetrieveStoredPipelines(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("listStoredPipelines", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        pipelines = ConfigStorage.listStoredPipelines()

        return CommandRes.okWithRes(json.dumps(pipelines))


class RequestStoredPipeline(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("requestStoredPipeline", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        pipeline = ConfigStorage.loadStoredPipeline(data["name"])

        if pipeline is None:
            return CommandRes.error("Couldn't load pipeline!")

        return CommandRes.okWithRes(json.dumps(pipeline))


class DeleteStoredPipeline(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("deleteStoredPipeline", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        removed = ConfigStorage.deleteStoredPipeline(data["name"])

        if not removed:
            return CommandRes.error("Failed to remove pipeline!")

        return CommandRes.ok()


class StorePipeline(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("storePipeline", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        stored = ConfigStorage.storePipeline(data["name"], data["data"])

        if not stored:
            return CommandRes.error("Failed to store pipeline!")

        return CommandRes.ok()


class RetrieveStoredOperators(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("listStoredOperators", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        ops = ConfigStorage.listStoredOperators()

        return CommandRes.okWithRes(json.dumps(ops))


class DeleteStoredOperator(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("deleteStoredOperator", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        removed = ConfigStorage.deleteStoredOperator(data["name"])

        if not removed:
            return CommandRes.error("Failed to delete operator preset!")

        return CommandRes.ok()


class StoreOperator(Command):
    def __init__(self, networkMode: NetworkMode):
        super().__init__("storeOperator", networkMode)

    def handleCommand(self, rm: RuntimeManager, data: Dict) -> CommandRes:
        stored = ConfigStorage.storeOperator(data)

        if not stored:
            return CommandRes.error("Couldn't store operator preset!")

        return CommandRes.ok()
