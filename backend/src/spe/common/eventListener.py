from typing import Dict, Callable, List


class EventListener:
    def __init__(self):
        self._map: Dict[str, List[Callable]] = dict()

    def register(self, event: str, function: Callable):
        if event in self._map:
            self._map.get(event).append(function)
        else:
            self._map[event] = [function]

    def unregisterEvent(self, event: str):
        self._map.pop(event, None)

    def unregisterFunction(self, event: str, function: Callable):
        listener = self._map.get(event)

        if listener is not None:
            listener.remove(function)

            if len(listener) == 0:
                self.unregisterEvent(event)

    def execute(self, event: str, arguments: list):
        listener = self._map.get(event)
        if listener is not None:
            for li in listener:
                li(*arguments)
