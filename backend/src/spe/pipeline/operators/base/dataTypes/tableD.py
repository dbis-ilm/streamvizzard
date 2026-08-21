from typing import List, Any

from spe.common.timer import Timer


class TableD(dict):
    def __init__(self, keys: List[str], entries: List[Any]):
        self.time = Timer.currentTime()

        self.keys = keys
        self.entries = entries

        # To allow JSON serialization
        dict.__init__(self, keys=self.keys, entries=self.entries, time=self.time)
