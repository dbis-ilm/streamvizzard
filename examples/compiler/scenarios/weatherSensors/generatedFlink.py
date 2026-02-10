"""
|--------------------------------------------------------|
| This code was generated automatically by StreamVizzard.|
|--------------------------------------------------------|
"""

from __future__ import annotations
import json
import timeit
from typing import Dict
from typing import Callable
from pyflink.common import Types
from pyflink.common import Encoder
from collections import defaultdict
from pyflink.common import Duration
from pyflink.common.time import Time
from pyflink.common import Configuration
from pyflink.common import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.functions import ProcessAllWindowFunction
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.datastream import RuntimeExecutionMode, TimeCharacteristic
from pyflink.datastream.connectors.file_system import FileSink, OutputFileConfig
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer

# Create the execution environment

config = Configuration()
config.set_integer("python.fn-execution.bundle.time", 1000)

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


kafkaSource_KafkaSource_1213 = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


def map_ParseJSON_1214(inTuple):
    return decodeJSON(inTuple)


def map_UDF_1212(inTuple):
    return inTuple


class ProcessWindowCollect1149(ProcessAllWindowFunction):
    def process(self, _, elements):
        yield list(elements)


def map_UDF_1146(inTuple):
    records = inTuple
    k = 2
    by_sensor = defaultdict(list)
    for r in records:
        by_sensor[r['sensorID']].append(r['avgT'])
    all_values = [v for vals in by_sensor.values() for v in vals]
    meanT = sum(all_values) / len(all_values)
    stdT = (sum(((v - meanT) ** 2 for v in all_values)) / len(all_values)) ** 0.5
    return ({sid: [v for v in vals if abs(v - meanT) > k * stdT] for sid, vals in by_sensor.items()},)[0]


def map_UDF_1210(inTuple):
    return ((inTuple, timeit.default_timer()),)[0]


def map_SerializeJSON_1145(inTuple):
    return encodeJSON(inTuple)


fs_FileSink_1144 = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("weatherOut").with_part_suffix(".txt").build()) \
    .build()


# ---------------- Pipeline Construction -----------------

KafkaSource_1213 = env.from_source(kafkaSource_KafkaSource_1213, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_1213', type_info=Types.STRING()).set_parallelism(1).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10)))
ParseJSON_1214 = KafkaSource_1213.map(map_ParseJSON_1214).set_parallelism(1)
UDF_1212 = ParseJSON_1214.map(map_UDF_1212).set_parallelism(1)
TumblingWindowTime_1148 = UDF_1212.window_all(TumblingProcessingTimeWindows.of(Time.milliseconds(2000)))
WindowCollect_1149 = TumblingWindowTime_1148.process(ProcessWindowCollect1149()).set_parallelism(1)
UDF_1146 = WindowCollect_1149.map(map_UDF_1146, output_type=Types.MAP(Types.INT(), Types.LIST(Types.DOUBLE()))).set_parallelism(1)
UDF_1210 = UDF_1146.map(map_UDF_1210).set_parallelism(1)
SerializeJSON_1145 = UDF_1210.map(map_SerializeJSON_1145, output_type=Types.STRING()).set_parallelism(1)
FileSink_1144 = SerializeJSON_1145.sink_to(fs_FileSink_1144).set_parallelism(1)

# Execute the pipeline

env.execute()
