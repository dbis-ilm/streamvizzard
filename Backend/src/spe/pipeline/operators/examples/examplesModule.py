from spe.pipeline.operators.module import Module


class ExamplesModule(Module):
    def __init__(self):
        super(ExamplesModule, self).__init__("Examples")

    def initialize(self):
        self.registerOp("spe.pipeline.operators.examples.laserWelding.lstmPredictionSL", "LstmPredictionSL",
                        "Laser Welding/LSTMPredictionSL")
        self.registerOp("spe.pipeline.operators.examples.laserWelding.cnnPredictionSL", "CNNPredictionSL",
                        "Laser Welding/CNNPredictionSL")
