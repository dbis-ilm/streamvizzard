from spe.common.timer import Timer


class ScatterplotD(dict):
    def __init__(self, plots: list):
        # This might contain multiple plots [ [], [] ]
        # Each plot contains of an array of elements, either one axis or two axis [,] or []

        self.time = Timer.currentTime()
        self.plots = plots

        # To allow JSON serialization
        dict.__init__(self, plots=plots, time=self.time)

    @staticmethod
    def fromElement(element):
        plot = [element]

        plots = [plot]

        return ScatterplotD(plots)

    @staticmethod
    def fromElements(elements):
        plots = [elements]

        return ScatterplotD(plots)
