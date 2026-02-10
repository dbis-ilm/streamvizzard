from __future__ import annotations

import json

import numpy
import timeit
from pyflink.common import Types
from pyflink.common import Encoder
from pyflink.common import Duration
from pyflink.common import Configuration
from pyflink.common import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment, MapFunction
from pyflink.common.serialization import SimpleStringSchema
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

kafkaSourceDef = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics(f"my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


class Sinkhorn(MapFunction):
    def map(self, data):
        tupIn = json.loads(data)

        hist_a = tupIn[0]
        hist_b = tupIn[1]
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


def finalizeData(inTuple):
    return json.dumps((inTuple, timeit.default_timer()))


fileSinkDef = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("imageOut").with_part_suffix(".txt").build()) \
    .build()


# ---------------- Pipeline Construction -----------------

KafkaSource = (env.from_source(kafkaSourceDef, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource', type_info=Types.STRING()).set_parallelism(3)
               .assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10))).set_parallelism(3).rebalance())
Process = KafkaSource.map(Sinkhorn(), output_type=Types.DOUBLE()).set_parallelism(3)
Finalize = Process.map(finalizeData, output_type=Types.STRING()).set_parallelism(1)
FileSink = Finalize.sink_to(fileSinkDef).set_parallelism(1)

env.execute()
