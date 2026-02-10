from __future__ import annotations

import zlib
import json
import pickle
import timeit

import pandas
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
config.set_integer("python.fn-execution.bundle.size", 500)  # Optimized

env = StreamExecutionEnvironment.get_execution_environment(config)
env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
env.set_stream_time_characteristic(TimeCharacteristic.ProcessingTime)

# ---------------------- Operators -----------------------

# PM
kafkaSourcePM = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics(f"my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()

# Weather
kafkaSourceWeather = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics(f"my-topic2") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


def parseJSON(inTuple):
    return json.loads(inTuple)


class ProcessWindow(ProcessWindowFunction):
    def process(self, key, _, elements):
        yield list(elements)


class JoinStreams(CoProcessFunction):
    def __init__(self):
        self.s1Buffer = []
        self.s2Buffer = []

    def process_element1(self, value, _):
        self.s1Buffer.append(value)

        if len(self.s2Buffer) > 0:
            v1 = self.s1Buffer.pop(0)
            v2 = self.s2Buffer.pop(0)

            yield self.process(v1, v2)

    def process_element2(self, value, _):
        self.s2Buffer.append(value)

        if len(self.s1Buffer) > 0:
            v1 = self.s1Buffer.pop(0)
            v2 = self.s2Buffer.pop(0)

            yield self.process(v1, v2)

    def process(self, val1, val2):
        weatherD = val1
        pmD = val2
        freq = '30s'
        t = pandas.DataFrame(weatherD)
        p = pandas.DataFrame(pmD)
        t['created_at'] = pandas.to_datetime(t['created_at'], utc=True)
        p['created_at'] = pandas.to_datetime(p['created_at'], utc=True)
        t = t.set_index('created_at').sort_index().resample(freq).mean()
        p = p.set_index('created_at').sort_index().resample(freq).mean()
        df = t.join(p, how='outer', lsuffix='_t', rsuffix='_p').sort_index()
        df = df.interpolate(limit_direction='both')

        df = df.sort_values('created_at').copy()
        df['temp_pm_corr'] = df['temperature_t'].expanding(
            min_periods=10).corr(df['dust_pm2_5'])
        return (df['temp_pm_corr'].tolist()[-1],)[0]


def finalize(inTuple):
    return json.dumps((inTuple, timeit.default_timer()))


fileSinkDef = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("weatherOut").with_part_suffix(".txt").build()) \
    .build()


# ---------------- Pipeline Construction -----------------

keys = [0, 1, 2]

KafkaSourcePM = env.from_source(kafkaSourcePM, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_1162', type_info=Types.STRING()).set_parallelism(3).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10))).set_parallelism(3)
KafkaSourceWeather = env.from_source(kafkaSourceWeather, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_1136', type_info=Types.STRING()).set_parallelism(3).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10))).set_parallelism(3)

ParseWeather = KafkaSourceWeather.map(parseJSON).set_parallelism(3).filter(lambda x: x['temperature'] is not None).set_parallelism(3)
WindowWeather = ParseWeather.set_max_parallelism(3).key_by(lambda x: keys[(zlib.crc32(pickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)) % 3) % len(keys)], key_type=Types.INT()).window(CountTumblingWindowAssigner.of(2000))
CollectWeather = WindowWeather.process(ProcessWindow(), output_type=Types.LIST(Types.PICKLED_BYTE_ARRAY())).set_parallelism(3)

ParsePM = KafkaSourcePM.map(parseJSON).set_parallelism(3).filter(lambda x: x['dust_pm2_5'] is not None).set_parallelism(3)
WindowPM = ParsePM.set_max_parallelism(3).key_by(lambda x: keys[(zlib.crc32(pickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)) % 3) % len(keys)], key_type=Types.INT()).window(CountTumblingWindowAssigner.of(1000))
CollectPM = WindowPM.process(ProcessWindow(), output_type=Types.LIST(Types.PICKLED_BYTE_ARRAY())).set_parallelism(3)

Join = CollectWeather.connect(CollectPM).process(JoinStreams(), output_type=Types.DOUBLE()).set_parallelism(3)
Finalize = Join.map(finalize, output_type=Types.STRING()).set_parallelism(1)
FileSink = Finalize.sink_to(fileSinkDef).set_parallelism(1)

# Execute the pipeline

env.execute()

