import asyncio
import json
import threading
from typing import List, Optional, Callable

from config import NETWORKING_SERVER_PORT, NETWORKING_SOCKET_PORT
from network import server
from spe.pipeline.pipelineUpdates import PipelineUpdate
from spe.pipeline.pipelineParser import PipelineManager
from spe.runtime.runtimeManager import RuntimeManager
from utils.utils import BColors, isWindowsOS


_shutdownHooks: List[Callable] = []


class StreamVizzard:
    def __init__(self):
        self.serverManager: Optional[server.ServerManager] = None
        self.pipelineManager: Optional[PipelineManager] = None
        self.runtimeManager: Optional[RuntimeManager] = None

        self.systemStartedEvent = threading.Event()

    def startUp(self):
        print("  _____  _                             __      __ _                           _ \r\n / ____|| |                            \\ \\    / /(_)                         | |\r\n| (___  | |_  _ __  ___   __ _  _ __ ___\\ \\  / /  _  ____ ____ __ _  _ __  __| |\r\n \\___ \\ | __|| \'__|/ _ \\ / _` || \'_ ` _ \\\\ \\/ /  | ||_  /|_  // _` || \'__|/ _` |\r\n ____) || |_ | |  |  __/| (_| || | | | | |\\  /   | | / /  / /| (_| || |  | (_| |\r\n|_____/  \\__||_|   \\___| \\__,_||_| |_| |_| \\/    |_|/___|/___|\\__,_||_|   \\__,_|\r\n                                                                                ")
        print("Starting system..")

        if isWindowsOS():
            from utils.asyncioUtils import windowsAsyncSleep
            asyncio.sleep = windowsAsyncSleep

        self.serverManager = server.ServerManager()
        self.pipelineManager = PipelineManager()
        self.runtimeManager = RuntimeManager(self.serverManager)

        apiThread, socketThread = self.serverManager.start(NETWORKING_SERVER_PORT, NETWORKING_SOCKET_PORT, self)

        self.systemStartedEvent.set()

        print("\n" + BColors.OKGREEN + "System started" + BColors.ENDC)

        # Keep main thread running until manual shutdown
        socketThread.join()

        self.systemStartedEvent.clear()

        print("System shutdown")

    def onPipelineStart(self, data: json):
        pipeline = self.pipelineManager.createPipeline(data["pipeline"])

        if pipeline is not None:
            self.runtimeManager.startPipeline(pipeline)

            self._applyStartMetaData(data["meta"])

    def onPipelineUpdated(self, data: json):
        updateID = data["updateID"]
        updates: List[PipelineUpdate] = list()

        for d in data["updates"]:
            upData = PipelineUpdate.parse(d, updateID)

            if upData is not None:
                updates.append(upData)

        self.runtimeManager.updatePipeline(updates)

    def onHeatmapChanged(self, data: json):
        self.runtimeManager.changeHeatmap(data["hmType"])

    def onDebuggerStepChange(self, data: json):
        self.runtimeManager.changeDebuggerStep(data["targetStep"], data["targetBranch"])

    def onDebuggerRequestStep(self, data: json):
        self.runtimeManager.requestDebuggerStep(data["targetBranch"], data["targetTime"])

    def onDebuggerStateChanged(self, data: json):
        self.runtimeManager.changeDebuggerState(data["historyActive"], data["historyRewind"])

    def onDebuggerConfigChanged(self, data: json):
        self.runtimeManager.changeDebuggerConfig(data["enabled"], data["debuggerMemoryLimit"], data["debuggerStorageLimit"],
                                                 data["historyRewindSpeed"], data["historyRewindUseStepTime"])

    def onAdvisorToggled(self, data: json):
        self.runtimeManager.toggleAdvisor(data["enabled"])

    def onPipelineStop(self, data: json):
        self.runtimeManager.shutdown()

    def _applyStartMetaData(self, metaData: json):
        self.runtimeManager.toggleAdvisor(metaData["advisorEnabled"])
        self.runtimeManager.changeHeatmap(metaData["heatmapType"])
        self.runtimeManager.changeDebuggerConfig(metaData["debuggerEnabled"], metaData["debuggerMemoryLimit"], metaData["debuggerStorageLimit"],
                                                 metaData["historyRewindSpeed"], metaData["historyRewindUseStepTime"])
        self.runtimeManager.changeDebuggerState(False, None)

    def shutdown(self):
        self.runtimeManager.shutdown()

        # Other hooks
        for hook in _shutdownHooks:
            hook()

        self.serverManager.shutdown()

    def __del__(self):
        self.shutdown()

    @staticmethod
    def registerShutdownHook(hook: Callable):
        _shutdownHooks.append(hook)
