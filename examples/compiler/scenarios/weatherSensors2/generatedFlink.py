"""
|--------------------------------------------------------|
| This code was generated automatically by StreamVizzard.|
|--------------------------------------------------------|
"""

from __future__ import annotations
import zlib
import json
import pickle
import timeit
import pandas
from typing import Dict
from typing import Callable
from pyflink.common import Types
from pyflink.common import Encoder
from pyflink.common import Duration
from pyflink.common import Configuration
from pyflink.common import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import CoProcessFunction
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.functions import ProcessWindowFunction
from pyflink.datastream.window import CountTumblingWindowAssigner
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


class StreamBufferedJoinFunction(CoProcessFunction):
    def __init__(self):
        self.s1Buffer = []
        self.s2Buffer = []

    def process_element1(self, value, _):
        self.s1Buffer.append(value)

        if len(self.s2Buffer) > 0:
            v1 = self.s1Buffer.pop(0)
            v2 = self.s2Buffer.pop(0)

            yield v1, v2

    def process_element2(self, value, _):
        self.s2Buffer.append(value)

        if len(self.s1Buffer) > 0:
            v1 = self.s1Buffer.pop(0)
            v2 = self.s2Buffer.pop(0)

            yield v1, v2


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


kafkaSource_KafkaSource_1162 = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


kafkaSource_KafkaSource_1136 = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic2") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


def map_ParseJSON_990(inTuple):
    return decodeJSON(inTuple)


def map_ParseJSON_1163(inTuple):
    return decodeJSON(inTuple)


def filter_Filter_1227(inTuple):
    return inTuple['dust_pm2_5'] is not None


keys_1164_3 = [0, 1, 2]


class ProcessWindowCollect1165(ProcessWindowFunction):
    def process(self, key, _, elements):
        yield list(elements)


def filter_Filter_1226(inTuple):
    return inTuple['temperature'] is not None


keys_1154_3 = [0, 1, 2]


class ProcessWindowCollect1156(ProcessWindowFunction):
    def process(self, key, _, elements):
        yield list(elements)


def map_UDF_1158(inTuple):
    weatherD = inTuple[0]
    pmD = inTuple[1]
    freq = '30s'
    t = pandas.DataFrame(weatherD)
    p = pandas.DataFrame(pmD)
    t['created_at'] = pandas.to_datetime(t['created_at'], utc=True)
    p['created_at'] = pandas.to_datetime(p['created_at'], utc=True)
    t = t.set_index('created_at').sort_index().resample(freq).mean()
    p = p.set_index('created_at').sort_index().resample(freq).mean()
    df = t.join(p, how='outer', lsuffix='_t', rsuffix='_p').sort_index()
    df = df.interpolate(limit_direction='both')
    return (df.reset_index(),)[0]


def map_UDF_1159(inTuple):
    df = inTuple.sort_values('created_at').copy()
    df['temp_pm_corr'] = df['temperature_t'].expanding(
        min_periods=10).corr(df['dust_pm2_5'])
    return (df['temp_pm_corr'].tolist()[-1],)[0]


def map_UDF_1228(inTuple):
    return ((inTuple, timeit.default_timer()),)[0]


def map_SerializeJSON_1160(inTuple):
    return encodeJSON(inTuple)


fs_FileSink_1161 = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("weatherOut").with_part_suffix(".txt").build()) \
    .build()


# ---------------- Pipeline Construction -----------------

KafkaSource_1162 = env.from_source(kafkaSource_KafkaSource_1162, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_1162', type_info=Types.STRING()).set_parallelism(3).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10))).set_parallelism(3)
KafkaSource_1136 = env.from_source(kafkaSource_KafkaSource_1136, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_1136', type_info=Types.STRING()).set_parallelism(3).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10))).set_parallelism(3)
ParseJSON_990 = KafkaSource_1136.map(map_ParseJSON_990).set_parallelism(3)
ParseJSON_1163 = KafkaSource_1162.map(map_ParseJSON_1163).set_parallelism(3)
Filter_1227 = ParseJSON_1163.filter(filter_Filter_1227).set_parallelism(3)
TumblingWindowCount_1164 = Filter_1227.key_by(lambda x: keys_1164_3[zlib.crc32(pickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)) % 3], key_type=Types.INT()).window(CountTumblingWindowAssigner.of(1000))
WindowCollect_1165 = TumblingWindowCount_1164.process(ProcessWindowCollect1165(), output_type=Types.LIST(Types.PICKLED_BYTE_ARRAY())).set_parallelism(3)
Filter_1226 = ParseJSON_990.filter(filter_Filter_1226).set_parallelism(3)
TumblingWindowCount_1154 = Filter_1226.key_by(lambda x: keys_1154_3[zlib.crc32(pickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)) % 3], key_type=Types.INT()).window(CountTumblingWindowAssigner.of(2000))
WindowCollect_1156 = TumblingWindowCount_1154.process(ProcessWindowCollect1156(), output_type=Types.LIST(Types.PICKLED_BYTE_ARRAY())).set_parallelism(3)
Join_1229 = WindowCollect_1156.connect(WindowCollect_1165).process(StreamBufferedJoinFunction(), output_type=Types.TUPLE([Types.LIST(Types.PICKLED_BYTE_ARRAY()), Types.LIST(Types.PICKLED_BYTE_ARRAY())])).set_parallelism(3)
UDF_1158 = Join_1229.map(map_UDF_1158).set_parallelism(3)
UDF_1159 = UDF_1158.map(map_UDF_1159, output_type=Types.DOUBLE()).set_parallelism(3)
UDF_1228 = UDF_1159.map(map_UDF_1228, output_type=Types.TUPLE([Types.DOUBLE(), Types.DOUBLE()])).set_parallelism(1)
SerializeJSON_1160 = UDF_1228.map(map_SerializeJSON_1160, output_type=Types.STRING()).set_parallelism(1)
FileSink_1161 = SerializeJSON_1160.sink_to(fs_FileSink_1161).set_parallelism(1)

# Execute the pipeline

env.execute()

