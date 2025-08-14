from typing import List, Iterator

from pympler import asizeof

from spe.common.tuple import Tuple


class Window:
    # Window tuples always have one input
    def __init__(self, tuples: List[Tuple]):
        self._tuples = tuples

    def getDataAt(self, idx):
        return self._tuples[idx].data[0]

    def getTupleAt(self, idx) -> Tuple:
        return self._tuples[idx]

    def getTuples(self) -> List[Tuple]:
        return self._tuples

    def getCount(self) -> int:
        return len(self._tuples)

    def iterateData(self) -> Iterator:
        for tup in self._tuples:
            yield tup.data[0]

    def toDataArray(self) -> list:
        return [t.data[0] for t in self._tuples]

    def isTypeOf(self, t):
        return len(self._tuples) > 0 and isinstance(self._tuples[0].data[0], t)

    def getDataSize(self) -> bytes:
        return asizeof.asizeof(self.toDataArray())
