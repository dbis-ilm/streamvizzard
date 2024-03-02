from enum import Enum


class HistoryState(Enum):
    INACTIVE = 1  # Pipeline is running
    ACTIVE = 2  # Pipeline stopped
    TRAVERSING_FORWARD = 3  # Pipeline stopped and traversing fwd
    TRAVERSING_BACKWARD = 4  # Pipeline stopped and traversing bwd

    def isActive(self) -> bool:
        return self != HistoryState.INACTIVE

    def isTraversing(self) -> bool:
        return self == HistoryState.TRAVERSING_BACKWARD or self == HistoryState.TRAVERSING_FORWARD
