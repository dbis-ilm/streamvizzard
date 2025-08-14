"""
|--------------------------------------------------------|
| This code was generated automatically by StreamVizzard.|
|--------------------------------------------------------|
"""

from __future__ import annotations
import json
import time
import heapq
import timeit
import statistics
import numpy as np
from typing import Dict
from typing import Callable
from pyflink.common import Types
from pyflink.common import Encoder
from pyflink.common import Duration
from pyflink.common import Configuration
from pyflink.common import WatermarkStrategy
from pyflink.datastream.functions import MapFunction
from pyflink.datastream import KeyedCoProcessFunction
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import TimestampAssigner
from pyflink.datastream.functions import ProcessAllWindowFunction
from pyflink.datastream.window import CountTumblingWindowAssigner
from pyflink.datastream import RuntimeExecutionMode, TimeCharacteristic
from pyflink.datastream.connectors.file_system import FileSink, OutputFileConfig
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer

# Create the execution environment

config = Configuration()
config.set_integer("python.fn-execution.bundle.time", 1000)

env = StreamExecutionEnvironment.get_execution_environment(config)
env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
env.set_stream_time_characteristic(TimeCharacteristic.EventTime)

# ------------------------ Utils -------------------------


class StreamBufferedOrderedJoinFunction(KeyedCoProcessFunction):
    def __init__(self, timerInterval):
        self.timerInterval = timerInterval
        self.timerRegistered = False

        # heap of (eventTime, tuple)
        self.s1Buffer = []
        self.s2Buffer = []

    def process_element1(self, value, ctx: KeyedCoProcessFunction.Context):
        eventTime = ctx.timestamp()

        # Buffer the event
        heapq.heappush(self.s1Buffer, (eventTime, value))

        self.setupTimer(ctx)

    def process_element2(self, value, ctx: KeyedCoProcessFunction.Context):
        eventTime = ctx.timestamp()

        # Buffer the event
        heapq.heappush(self.s2Buffer, (eventTime, value))

        self.setupTimer(ctx)

    def setupTimer(self, ctx: KeyedCoProcessFunction.Context):
        # Register a timer if none is registered

        if not self.timerRegistered:
            triggerTime = ctx.timer_service().current_watermark() + self.timerInterval
            ctx.timer_service().register_event_time_timer(triggerTime)
            self.timerRegistered = True

    def on_timer(self, timestamp: int, ctx: KeyedCoProcessFunction.OnTimerContext):
        watermark = ctx.timer_service().current_watermark()

        # Emit all tuple pairs where eventTime <= watermark

        while (self.s1Buffer and self.s2Buffer and
               self.s1Buffer[0][0] <= watermark and
               self.s2Buffer[0][0] <= watermark):
            eventTime1, value1 = heapq.heappop(self.s1Buffer)
            eventTime2, value2 = heapq.heappop(self.s2Buffer)

            yield value1, value2

        # Check if we still have buffered elements and schedule next timer

        if self.s1Buffer and self.s2Buffer:
            trigger_time = watermark + self.timerInterval
            ctx.timer_service().register_event_time_timer(trigger_time)
            self.timerRegistered = True
        else:
            # No more elements, clear timer flag
            self.timerRegistered = False


class EventTimeAssigner(TimestampAssigner):
    def __init__(self):
        self.counter = 0

    def extract_timestamp(self, value, record_timestamp: int) -> int:
        self.counter += 1

        return int(time.time() * 1000) + self.counter


customJSONDeserializer: Dict[str, Callable] = dict()


def encodeJSON(data):
    return json.dumps(data, default=jsonSerializer)


def jsonSerializer(data):
    if hasattr(data, 'toJSON'):
        return {'type': type(data).__name__, 'data': data.toJSON()}
    return data


def decodeJSON(data: str):
    return json.loads(data, object_hook=jsonDeserializer)


def jsonDeserializer(data):
    if 'type' not in data:
        return data
    dataType = data['type']
    dataVal = data['data']
    des = customJSONDeserializer.get(dataType, None)
    if des is not None:
        return des(dataVal)
    return dataVal

# ---------------------- Operators -----------------------


kafkaSource_KafkaSource_1065 = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("conGroup") \
    .set_topics("my-topic2") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


def map_ParseJSON_1066(inTuple):
    return decodeJSON(inTuple)


kafkaSource_KafkaSource_1064 = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


def map_ParseJSON_522(inTuple):
    return decodeJSON(inTuple)


class ProcessAllWindowCollect975(ProcessAllWindowFunction):
    def process(self, _, elements):
        yield list(elements)


class LstmOp1008(MapFunction):
    def __init__(self):
        self.modelPath = "/home/pyflink/lstm.hdf5"
        self.predictSteps = 100

        self._currentModel = None

    def open(self, ctx):
        from tensorflow import keras

        def _root_mean_squared_error(y_true, y_pred):
            return keras.backend.sqrt(keras.backend.mean(keras.backend.square(y_pred - y_true)))

        def _get_inference_model(model, latent_dim=256):
            encoder_inputs = model.input[0]  # input_1
            # lstm_1
            encoder_outputs, state_h_enc, state_c_enc = model.layers[2].output
            encoder_states = [state_h_enc, state_c_enc]
            encoder_model = keras.Model(encoder_inputs, encoder_states)

            decoder_inputs = model.input[1]  # input_2
            decoder_state_input_h = keras.Input(
                shape=(latent_dim,), name="input_3")
            decoder_state_input_c = keras.Input(
                shape=(latent_dim,), name="input_4")
            decoder_states_inputs = [
                decoder_state_input_h, decoder_state_input_c]
            decoder_lstm = model.layers[3]
            decoder_outputs, state_h_dec, state_c_dec = decoder_lstm(
                decoder_inputs, initial_state=decoder_states_inputs
            )
            decoder_states = [state_h_dec, state_c_dec]
            decoder_dense = model.layers[4]
            decoder_outputs = decoder_dense(decoder_outputs)
            decoder_model = keras.Model(
                [decoder_inputs] +
                decoder_states_inputs, [decoder_outputs] + decoder_states
            )

            return encoder_model, decoder_model

        regression_model = keras.models.load_model(
            self.modelPath, compile=False)
        regression_model.compile(loss=_root_mean_squared_error)
        encoderModel, decoderModel = _get_inference_model(regression_model)
        self._currentModel = (encoderModel, decoderModel)

    def _predict(self, input_data, output_steps):
        h, c = self._currentModel[0].predict(
            np.array([input_data]), verbose=None)
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


map_LstmPredictionSL_1008 = LstmOp1008()


def map_UDF_668(inTuple):
    dataLstm = inTuple[0][0]
    dataCnn = inTuple[1]
    return ((statistics.mean(dataLstm) + dataCnn, timeit.default_timer()),)[0]


fs_FileSink_674 = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("laserWeldingOut").with_part_suffix(".txt").build()) \
    .build()


# ---------------- Pipeline Construction -----------------

KafkaSource_1065 = env.from_source(kafkaSource_KafkaSource_1065, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_1065', type_info=Types.STRING()).set_parallelism(1).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10)).with_timestamp_assigner(EventTimeAssigner())).set_parallelism(1)
ParseJSON_1066 = KafkaSource_1065.map(map_ParseJSON_1066, output_type=Types.DOUBLE()).set_parallelism(1)
KafkaSource_1064 = env.from_source(kafkaSource_KafkaSource_1064, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_1064', type_info=Types.STRING()).set_parallelism(1).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10)).with_timestamp_assigner(EventTimeAssigner())).set_parallelism(1)
ParseJSON_522 = KafkaSource_1064.map(map_ParseJSON_522, output_type=Types.LIST(Types.DOUBLE())).set_parallelism(1)
TumblingWindowCount_524 = ParseJSON_522.window_all(CountTumblingWindowAssigner.of(40))
WindowCollect_975 = TumblingWindowCount_524.process(ProcessAllWindowCollect975(), output_type=Types.LIST(Types.LIST(Types.DOUBLE()))).set_parallelism(1)
LstmPredictionSL_1008 = WindowCollect_975.map(map_LstmPredictionSL_1008, output_type=Types.LIST(Types.LIST(Types.DOUBLE()))).set_parallelism(5)
Join_1067 = LstmPredictionSL_1008.connect(ParseJSON_1066).key_by(lambda x: 1, lambda x: 1).process(StreamBufferedOrderedJoinFunction(env.get_config().get_auto_watermark_interval()), output_type=Types.TUPLE([Types.LIST(Types.LIST(Types.DOUBLE())), Types.DOUBLE()])).set_parallelism(1)
UDF_668 = Join_1067.map(map_UDF_668, output_type=Types.TUPLE([Types.DOUBLE(), Types.DOUBLE()])).set_parallelism(1)
FileSink_674 = UDF_668.sink_to(fs_FileSink_674).set_parallelism(1)

# Execute the pipeline

env.execute()
