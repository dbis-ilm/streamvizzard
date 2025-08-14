import asyncio
import json
from typing import Optional, List

import numpy as np
from tensorflow import keras

from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileLanguage, CompileComputeMode, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.common.tuple import Tuple
from spe.pipeline.operators.operator import Operator


# Stateless implementation based on input time-series

class LstmPredictionSL(Operator):
    def __init__(self, opID: int):
        super(LstmPredictionSL, self).__init__(opID, 1, 1)

        self.modelPath = ""
        self.predictSteps = 0

        self._currentModel = None

    def setData(self, data: json):
        self.modelPath = data["modelPath"]
        self.predictSteps = data["predictSteps"]

    def getData(self) -> dict:
        return {"modelPath": self.modelPath, "predictSteps": self.predictSteps}

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super(LstmPredictionSL, self).onRuntimeCreate(eventLoop)

        # Try load the model

        try:
            regression_model = keras.models.load_model(self.modelPath, compile=False)
            regression_model.compile(loss=lambda y_true, y_pred: keras.backend.sqrt(
                keras.backend.mean(keras.backend.square(y_pred - y_true))))
            encoderModel, decoderModel = self._get_inference_model(regression_model)
            self._currentModel = (encoderModel, decoderModel)
        except Exception:
            self.onExecutionError()

    @staticmethod
    def _get_inference_model(model, latent_dim=256):
        encoder_inputs = model.input[0]  # input_1
        encoder_outputs, state_h_enc, state_c_enc = model.layers[2].output  # lstm_1
        encoder_states = [state_h_enc, state_c_enc]
        encoder_model = keras.Model(encoder_inputs, encoder_states)

        decoder_inputs = model.input[1]  # input_2
        decoder_state_input_h = keras.Input(shape=(latent_dim,), name="input_3")
        decoder_state_input_c = keras.Input(shape=(latent_dim,), name="input_4")
        decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
        decoder_lstm = model.layers[3]
        decoder_outputs, state_h_dec, state_c_dec = decoder_lstm(
            decoder_inputs, initial_state=decoder_states_inputs
        )
        decoder_states = [state_h_dec, state_c_dec]
        decoder_dense = model.layers[4]
        decoder_outputs = decoder_dense(decoder_outputs)
        decoder_model = keras.Model(
            [decoder_inputs] + decoder_states_inputs, [decoder_outputs] + decoder_states
        )

        return encoder_model, decoder_model

    def _predict(self, input_data, output_steps):
        h, c = self._currentModel[0].predict(np.array([input_data]), verbose=None)
        states = [h, c]

        # Decoder prediction
        lstm_predictions = np.empty((output_steps, 3))
        next_input = np.empty((1, 1, 3), dtype=np.float32)
        next_input[0, 0, :] = input_data[-1]

        # Here is the bottleneck of the model (not optimized)
        for j in range(output_steps):
            output, h, c = self._currentModel[1]([next_input] + states)
            next_input = output
            states = [h, c]
            lstm_predictions[j] = output

        return lstm_predictions

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        if self._currentModel is None:
            return None

        matrix = np.array(tupleIn.data[0])

        # Predict values

        res = self._predict(matrix, self.predictSteps)

        if res is None:
            return None

        res = res.transpose()  # Receives array of columns

        # Convert from numpy array to python list and append the so far collected values to have correct curve
        inCols = matrix.transpose()
        resList = []

        for i in range(0, len(res)):
            resList.append(inCols[i].tolist() + res[i].tolist())

        return self.createTuple((resList,))

    # ---------------------------- COMPILATION ----------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(compileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.functions import MapFunction
            import numpy as np""",
                PyFlinkCodeTemplate.Section.FUNCTION_DECLARATION: f"""
            class LstmOp{self.id}(MapFunction):
                def __init__(self):
                    self.modelPath = \"{self.modelPath}\"
                    self.predictSteps = {self.predictSteps}

                    self._currentModel = None

                def open(self, ctx):
                    from tensorflow import keras

                    def _root_mean_squared_error(y_true, y_pred):
                        return keras.backend.sqrt(keras.backend.mean(keras.backend.square(y_pred - y_true)))

                    def _get_inference_model(model, latent_dim=256):
                        encoder_inputs = model.input[0]  # input_1
                        encoder_outputs, state_h_enc, state_c_enc = model.layers[2].output  # lstm_1
                        encoder_states = [state_h_enc, state_c_enc]
                        encoder_model = keras.Model(encoder_inputs, encoder_states)

                        decoder_inputs = model.input[1]  # input_2
                        decoder_state_input_h = keras.Input(shape=(latent_dim,), name="input_3")
                        decoder_state_input_c = keras.Input(shape=(latent_dim,), name="input_4")
                        decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
                        decoder_lstm = model.layers[3]
                        decoder_outputs, state_h_dec, state_c_dec = decoder_lstm(
                            decoder_inputs, initial_state=decoder_states_inputs
                        )
                        decoder_states = [state_h_dec, state_c_dec]
                        decoder_dense = model.layers[4]
                        decoder_outputs = decoder_dense(decoder_outputs)
                        decoder_model = keras.Model(
                            [decoder_inputs] + decoder_states_inputs, [decoder_outputs] + decoder_states
                        )

                        return encoder_model, decoder_model

                    regression_model = keras.models.load_model(self.modelPath, compile=False)
                    regression_model.compile(loss=_root_mean_squared_error)
                    encoderModel, decoderModel = _get_inference_model(regression_model)
                    self._currentModel = (encoderModel, decoderModel)

                def _predict(self, input_data, output_steps):
                    h, c = self._currentModel[0].predict(np.array([input_data]), verbose=None)
                    states = [h, c]

                    # Decoder prediction
                    lstm_predictions = np.empty((output_steps, 3))
                    next_input = np.empty((1, 1, 3), dtype=np.float32)
                    next_input[0, 0, :] = input_data[-1]

                    # Here is the bottleneck of the model (not optimized)
                    for j in range(output_steps):
                        output, h, c = self._currentModel[1]([next_input] + states)
                        next_input = output
                        states = [h, c]
                        lstm_predictions[j] = output

                    return lstm_predictions

                def map(self, tupleIn):
                    matrix = np.array(tupleIn)

                    # Predict values

                    # Receives array of columns
                    res = self._predict(matrix, self.predictSteps).transpose()

                    # Convert from numpy array to python list and append the so far collected values to have correct curve
                    inCols = matrix.transpose()
                    resList = []

                    for i in range(0, len(res)):
                        resList.append(inCols[i].tolist() + res[i].tolist())

                    return resList

            map_{self.getUniqueName()} = LstmOp{self.id}()
            """})

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.MAP, getPyFlinkCode))]
