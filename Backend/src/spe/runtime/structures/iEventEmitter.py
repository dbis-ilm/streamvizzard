from typing import Callable, List

from spe.runtime.structures.eventListener import EventListener


class IEventEmitter:
    def __init__(self):
        self._eventListener = EventListener()

    def getEventListener(self) -> EventListener:
        return self._eventListener

    def registerEvent(self, event: str, callback: Callable):
        self._eventListener.register(event, callback)

    def unregisterEvent(self, event: str, callback: Callable):
        self._eventListener.unregisterFunction(event, callback)

    def executeEvent(self, event: str, arguments: List):
        self._eventListener.execute(event, arguments)
