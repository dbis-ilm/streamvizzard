from __future__ import annotations
import pickle
import zlib
import json
import timeit
import statistics
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
import random

# Create the execution environment

config = Configuration()
config.set_integer("python.fn-execution.bundle.time", 1000)

env = StreamExecutionEnvironment.get_execution_environment(config)
env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
env.set_stream_time_characteristic(TimeCharacteristic.ProcessingTime)

# ------------------------ Operators -------------------------

kafkaProps = {
    # fetch tuning
    "fetch.min.bytes": "1048576",
    "fetch.max.wait.ms": "50",
    "max.partition.fetch.bytes": "8388608",
    "max.poll.records": "5000",
}

# To reach the desired performance, the utilized topic should feature 8 partitions!
KafkaSource = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic") \
    .set_properties(kafkaProps) \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()

class ProcessWindow(ProcessWindowFunction):
    def process(self, key, _, elements):
        data = [json.loads(d) for d in list(elements)]

        rows = data
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

        yield json.dumps({
            "avg": avg,
            "median": median,
            "stdDev": std,
            "avg_ci95": (boot_means[lo], boot_means[hi]),
            "median_ci95": (boot_medians[lo], boot_medians[hi]),
        })

def prepareOutput(inTuple):
    return (inTuple, timeit.default_timer())


fs_FileSink = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("energyOut").with_part_suffix(".txt").build()) \
    .build()

# ---------------- Pipeline Construction -----------------

KafkaSource_Op = (env.from_source(KafkaSource, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_778', type_info=Types.STRING())
                   .set_parallelism(8).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10))))

TumblingWindowCount_Op = (KafkaSource_Op
                            .key_by(lambda x: zlib.crc32(pickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)) % 8)
                            .window(CountTumblingWindowAssigner.of(5000)))

WindowProcess_Op = TumblingWindowCount_Op.process(ProcessWindow(), output_type=Types.STRING()).set_parallelism(8).rebalance()
PrepareOutput_Op = WindowProcess_Op.map(prepareOutput, output_type=Types.TUPLE([Types.STRING(), Types.DOUBLE()])).set_parallelism(1)
FileSink_686 = PrepareOutput_Op.sink_to(fs_FileSink).set_parallelism(1)

# Execute the pipeline

env.execute()
