from __future__ import annotations
import pickle
import zlib
import json
import timeit
import statistics
from typing import Dict
from typing import Callable
from pyflink.common import Types
from pyflink.common import Encoder
from pyflink.common import Duration
from pyflink.common import Configuration
from pyflink.common import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.window import CountTumblingWindowAssigner
from pyflink.datastream.functions import ProcessWindowFunction
from pyflink.datastream import RuntimeExecutionMode, TimeCharacteristic
from pyflink.datastream.connectors.file_system import FileSink, OutputFileConfig
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.datastream.functions import MapFunction
import random

# Create the execution environment

config = Configuration()
config.set_integer("python.fn-execution.bundle.time", 1000)

env = StreamExecutionEnvironment.get_execution_environment(config)
env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
env.set_stream_time_characteristic(TimeCharacteristic.ProcessingTime)

# ---------------------- Operators -----------------------

kafkaSource_KafkaSource_778 = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()

def map_ParseJSON_990(inTuple):
    return decodeJSON(inTuple)


class ProcessWindowCollect1176(ProcessWindowFunction):
    def process(self, key, _, elements):
        yield list(elements)

class Aggregation(MapFunction):
    def map(self, inTup):
        rows = inTup
        seed = 0
        B = 50

        rng = random.Random(seed)

        prices = [x for r in rows for x in r["prices"]]
        n = len(prices)

        avg = statistics.fmean(prices)
        median = statistics.median(prices)
        std = statistics.stdev(prices) if n > 1 else 0.0

        boot_means = []
        boot_medians = []
        for _ in range(B):
            sample = [prices[rng.randrange(n)] for _ in range(n)]
            boot_means.append(statistics.fmean(sample))
            boot_medians.append(statistics.median(sample))

        boot_means.sort()
        boot_medians.sort()
        lo = int(0.025 * (B - 1))
        hi = int(0.975 * (B - 1))

        return {
            "avg": avg,
            "median": median,
            "stdDev": std,
            "avg_ci95": (boot_means[lo], boot_means[hi]),
            "median_ci95": (boot_medians[lo], boot_medians[hi])
        }

def map_SerializeJSON_1177(inTuple):
    return encodeJSON(inTuple)


def map_UDF_1188(inTuple):
    return (inTuple, timeit.default_timer())


fs_FileSink_686 = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("energyOut").with_part_suffix(".txt").build()) \
    .build()

# ---------------- Pipeline Construction -----------------

KafkaSource_778 = (env.from_source(kafkaSource_KafkaSource_778, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_778', type_info=Types.STRING())
                   .set_parallelism(8).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10))))
ParseJSON_990 = KafkaSource_778.map(map_ParseJSON_990).set_parallelism(8)

TumblingWindowCount_1175 = (ParseJSON_990
                            .key_by(lambda x: zlib.crc32(pickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)) % 8)
                            .window(CountTumblingWindowAssigner.of(5000)))

WindowCollect_1176 = TumblingWindowCount_1175.process(ProcessWindowCollect1176(), output_type=Types.LIST(Types.PICKLED_BYTE_ARRAY())).set_parallelism(8).rebalance()

UDF_992 = WindowCollect_1176.map(Aggregation()).set_parallelism(8)
SerializeJSON_1177 = UDF_992.map(map_SerializeJSON_1177, output_type=Types.STRING()).set_parallelism(8)
UDF_1188 = SerializeJSON_1177.map(map_UDF_1188, output_type=Types.TUPLE([Types.STRING(), Types.DOUBLE()])).set_parallelism(1)
FileSink_686 = UDF_1188.sink_to(fs_FileSink_686).set_parallelism(1)

# Execute the pipeline

env.execute()
