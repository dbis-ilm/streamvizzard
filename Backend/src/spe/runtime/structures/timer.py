import timeit


class Timer:
    def __init__(self):
        self._timeOffset = 0  # In seconds

    @staticmethod
    def currentTime():
        return timeit.default_timer() + __timer__._timeOffset

    @staticmethod
    def currentRealTime():
        return timeit.default_timer()

    @staticmethod
    def offsetTime(offset: float):
        __timer__._timeOffset += offset

    @staticmethod
    def setTime(time: float):
        current = timeit.default_timer()

        __timer__._timeOffset = time - current

    @staticmethod
    def reset():
        __timer__._timeOffset = 0


__timer__ = Timer()
