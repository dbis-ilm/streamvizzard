from __future__ import annotations
import asyncio
import os.path
import pathlib
import threading
from typing import TYPE_CHECKING, List, Optional, Callable

from config import Config, NETWORKING_SOCKET_PORT, NETWORKING_SERVER_PORT
from utils.utils import BColors, isWindowsOS, parseBool

if TYPE_CHECKING:
    from spe.runtime.runtimeManager import RuntimeManager
    from network.server import ServerManager

_instance: Optional[StreamVizzard] = None


class StreamVizzard:
    def __init__(self, config: Config):
        self.serverManager: Optional[ServerManager] = None
        self.runtimeManager: Optional[RuntimeManager] = None

        self._running = False

        self._systemShutdownEvent = threading.Event()
        self._shutdownHooks: List[Callable] = []

        self._config = config

        global _instance
        _instance = self

    def start(self):
        if self._running:
            print("System already running!")

            return

        print("  _____  _                             __      __ _                           _ \r\n / ____|| |                            \\ \\    / /(_)                         | |\r\n| (___  | |_  _ __  ___   __ _  _ __ ___\\ \\  / /  _  ____ ____ __ _  _ __  __| |\r\n \\___ \\ | __|| \'__|/ _ \\ / _` || \'_ ` _ \\\\ \\/ /  | ||_  /|_  // _` || \'__|/ _` |\r\n ____) || |_ | |  |  __/| (_| || | | | | |\\  /   | | / /  / /| (_| || |  | (_| |\r\n|_____/  \\__||_|   \\___| \\__,_||_| |_| |_| \\/    |_|/___|/___|\\__,_||_|   \\__,_|\r\n                                                                                ")
        print("Starting system...")

        if isWindowsOS():
            # Patch asyncio sleep for windows
            from utils.asyncioUtils import windowsAsyncSleep
            asyncio.sleep = windowsAsyncSleep

        from spe.runtime.runtimeManager import RuntimeManager
        from network.server import ServerManager

        self.serverManager = ServerManager(self)
        self.runtimeManager = RuntimeManager(self.serverManager)

        if self._config.NETWORK_ENABLED:
            self.serverManager.start(NETWORKING_SERVER_PORT, NETWORKING_SOCKET_PORT)

        self._running = True

        print(BColors.OKGREEN + "System started" + BColors.ENDC + "\n")

    def keepRunning(self):
        """ Blocks until the system is (manually) shutdown. """

        try:
            # Allow the wait event to be interrupted
            while not self._systemShutdownEvent.wait(1):
                pass
        except KeyboardInterrupt:
            return

    def stopPipeline(self):
        self.runtimeManager.stopPipeline()

    def shutdown(self):
        if not self._running:
            return

        print("Stopping system...")

        self.runtimeManager.shutdown()

        # Other hooks
        for hook in self._shutdownHooks:
            hook()

        self.serverManager.shutdown()

        self._systemShutdownEvent.set()
        self._running = False

        print(BColors.OKBLUE + "System stopped" + BColors.ENDC)

    def __del__(self):
        self.shutdown()

    @staticmethod
    def registerShutdownHook(hook: Callable):
        if _instance is None:
            print("StreamVizzard system not running!")

            return

        _instance._shutdownHooks.append(hook)

    @staticmethod
    def getConfig() -> Optional[Config]:
        if _instance is None:
            print("StreamVizzard system not running!")

            return None

        return _instance._config

    @staticmethod
    def getRootPath():
        return str(pathlib.Path(__file__).parent.parent.resolve())

    @staticmethod
    def getRootSrcPath():
        return str(pathlib.Path(__file__).parent.resolve())

    @staticmethod
    def getOutPath():
        rootPath = StreamVizzard.getRootPath()

        return os.path.join(rootPath, "out")

    @staticmethod
    def requestOutFolder(*folders: str) -> str:
        outFolder = StreamVizzard.getOutPath()

        path = os.path.join(outFolder, *folders)

        os.makedirs(path, exist_ok=True)

        return path

    @staticmethod
    def isDockerExecution() -> bool:
        return parseBool(os.environ.get("DOCKER", "false"))
