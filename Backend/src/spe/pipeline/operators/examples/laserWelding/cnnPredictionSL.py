import asyncio
import json
from typing import Optional, List

import numpy as np
from tensorflow import keras

from spe.pipeline.operators.operator import Operator
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileLanguage, CompileComputeMode, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.common.tuple import Tuple


class CNNPredictionSL(Operator):

    def __init__(self, opID: int):
        super(CNNPredictionSL, self).__init__(opID, 1, 1)
        # Minimum and Maximum values based on training data
        self.minimum = 10372
        self.maximum = 39338

        self.modelPath = ""

        self._model = None

    def setData(self, data: json):
        self.modelPath = data["modelPath"]

    def getData(self) -> dict:
        return {"modelPath": self.modelPath}

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super(CNNPredictionSL, self).onRuntimeCreate(eventLoop)

        self._model = keras.models.load_model(self.modelPath)

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        if self._model is None:
            return None

        frame = tupleIn.data[0].mat

        # Normalize
        roi = (frame - self.minimum) / (self.maximum - self.minimum)

        # Reshape for CNN
        roi = np.reshape(roi, (1, 59, 9))

        # Predict Weld
        prediction = self._model.predict(roi, verbose=None)[0, 0]

        return self.createTuple((prediction.item(),))  # Converts numpy float to python float

    # ---------------------------- COMPILATION ----------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(compileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.functions import MapFunction
            import numpy as np""",
                PyFlinkCodeTemplate.Section.FUNCTION_DECLARATION: f"""
            class CnnOp{self.id}(MapFunction):
                def __init__(self):
                    self.modelPath = \"{self.modelPath}\"
                    self.minimum = {self.minimum}
                    self.maximum = {self.maximum}

                    self.model = None

                def open(self, ctx):
                    from tensorflow import keras

                    self.model = keras.models.load_model(self.modelPath)

                def map(self, tupleIn):
                    # Normalize
                    roi = (tupleIn - self.minimum) / (self.maximum - self.minimum)
            
                    # Reshape for CNN
                    roi = np.reshape(roi, (1, 59, 9))
            
                    # Predict Weld
                    prediction = self.model.predict(roi, verbose=None)[0, 0]
            
                    return prediction.item()  # Converts numpy float to python float

            map_{self.getUniqueName()} = CnnOp{self.id}()
            """})

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.MAP, getPyFlinkCode))]
