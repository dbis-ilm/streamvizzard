from abc import ABC

from spe.pipeline.operators.operator import Operator


class Sink(Operator, ABC):
    def __init__(self, opID: int, socketsIn: int):
        super().__init__(opID, socketsIn, 0)
