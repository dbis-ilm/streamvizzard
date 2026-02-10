"""
|--------------------------------------------------------|
| This code was generated automatically by StreamVizzard.|
|--------------------------------------------------------|
"""

from __future__ import annotations
import json
import numpy
import timeit
from typing import Dict
from typing import Callable
from pyflink.common import Types
from pyflink.common import Encoder
from pyflink.common import Duration
from pyflink.common import Configuration
from pyflink.common import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import RuntimeExecutionMode, TimeCharacteristic
from pyflink.datastream.connectors.file_system import FileSink, OutputFileConfig
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer

# Create the execution environment

config = Configuration()
config.set_integer("python.fn-execution.bundle.time", 1000)  # Default
config.set_integer("python.fn-execution.bundle.size", 1000)  # Default

env = StreamExecutionEnvironment.get_execution_environment(config)
env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
env.set_stream_time_characteristic(TimeCharacteristic.ProcessingTime)

# ------------------------ Utils -------------------------


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


kafkaSource_KafkaSource_1296 = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


def map_ParseJSON_1297(inTuple):
    return decodeJSON(inTuple)


def map_UDF_1292(inTuple):
    hist_a = inTuple[0]
    hist_b = inTuple[1]
    eps = 0.05
    iters = 200
    a = numpy.asarray(hist_a, float)
    a /= a.sum()
    b = numpy.asarray(hist_b, float)
    b /= b.sum()
    x = numpy.arange(256)
    C = (x[:, None] - x[None, :]) ** 2
    K = numpy.exp(-C / eps)
    u = numpy.ones(256)
    v = numpy.ones(256)
    for _ in range(iters):
        u = a / (K @ v + 1e-12)
        v = b / (K.T @ u + 1e-12)
    P = u[:, None] * K * v[None, :]
    sinkhornOt = float((P * C).sum())
    return (sinkhornOt,)[0]


def map_UDF_1293(inTuple):
    sinkhorn = inTuple
    return ((sinkhorn, timeit.default_timer()),)[0]


def map_SerializeJSON_1295(inTuple):
    return encodeJSON(inTuple)


fs_FileSink_1294 = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("imageOut").with_part_suffix(".txt").build()) \
    .build()


# ---------------- Pipeline Construction -----------------

KafkaSource_1296 = env.from_source(kafkaSource_KafkaSource_1296, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_1296', type_info=Types.STRING()).set_parallelism(3).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10))).set_parallelism(3)
ParseJSON_1297 = KafkaSource_1296.map(map_ParseJSON_1297, output_type=Types.LIST(Types.LIST(Types.DOUBLE()))).set_parallelism(3)
UDF_1292 = ParseJSON_1297.map(map_UDF_1292, output_type=Types.DOUBLE()).set_parallelism(3)
UDF_1293 = UDF_1292.map(map_UDF_1293, output_type=Types.TUPLE([Types.DOUBLE(), Types.DOUBLE()])).set_parallelism(1)
SerializeJSON_1295 = UDF_1293.map(map_SerializeJSON_1295, output_type=Types.STRING()).set_parallelism(1)
FileSink_1294 = SerializeJSON_1295.sink_to(fs_FileSink_1294).set_parallelism(1)

# Execute the pipeline

env.execute()
