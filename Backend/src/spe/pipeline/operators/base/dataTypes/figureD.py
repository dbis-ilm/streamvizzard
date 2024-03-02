from numbers import Number
from typing import List, Tuple, Union, Optional

from spe.pipeline.operators.imageProc.dataTypes.image import Image


class LineD:
    def __init__(self, points: List[Tuple[Number, Number]], width: Number,
                 color: Union[Tuple[Number, Number, Number, Number],
                              Tuple[Number, Number, Number]], updated: bool = True):
        self.points = points
        self.color = color
        self.width = width

        self.updated = updated

    def toDict(self):
        return {"points": self.points, "color": self.color, "width": self.width}


class FigureD:
    def __init__(self, size: Tuple[Number, Number], bgImg: Optional[Image], updateImg: bool, lines: List[LineD]):
        self.bgImg = bgImg
        self.updateImg = updateImg
        self.lines = lines

        self.size = size

    def toDict(self):
        return {"size": self.size, "bgImg": self.bgImg, "updateImg": self.updateImg, "lines": [line.toDict() for line in self.lines]}
