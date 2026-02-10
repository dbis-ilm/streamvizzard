from __future__ import annotations

import json
import timeit
from pyflink.common import Types
from pyflink.common import Encoder
from pyflink.common import Duration
from collections import defaultdict
from pyflink.common.time import Time
from pyflink.common import Configuration
from pyflink.common import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.datastream.functions import ProcessAllWindowFunction
from pyflink.datastream import RuntimeExecutionMode, TimeCharacteristic
from pyflink.datastream.connectors.file_system import FileSink, OutputFileConfig
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer

# Create the execution environment

config = Configuration()
config.set_integer("python.fn-execution.bundle.time", 1000)

env = StreamExecutionEnvironment.get_execution_environment(config)
env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
env.set_stream_time_characteristic(TimeCharacteristic.ProcessingTime)

# ---------------------- Operators -----------------------

kafkaSource = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


class ProcessWindow(ProcessAllWindowFunction):
    def process(self, _, elements):
        records = [json.loads(d) for d in list(elements)]
        k = 2

        by_sensor = defaultdict(list)
        for r in records:
            by_sensor[r['sensorID']].append(r['avgT'])
        all_values = [v for vals in by_sensor.values() for v in vals]
        meanT = sum(all_values) / len(all_values)
        stdT = (sum(((v - meanT) ** 2 for v in all_values)) / len(all_values)) ** 0.5

        yield json.dumps(({sid: [v for v in vals if abs(v - meanT) > k * stdT] for sid, vals in by_sensor.items()}, timeit.default_timer()))

fs_FileSink = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("weatherOut").with_part_suffix(".txt").build()) \
    .build()

# ---------------- Pipeline Construction -----------------

KafkaSource = (env.from_source(kafkaSource, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource', type_info=Types.STRING())
                    .set_parallelism(1).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10))))
TumblingWindow = KafkaSource.window_all(TumblingProcessingTimeWindows.of(Time.milliseconds(2000)))
WindowProcess = TumblingWindow.process(ProcessWindow(), output_type=Types.STRING()).set_parallelism(1)
FileSink = WindowProcess.sink_to(fs_FileSink).set_parallelism(1)

# Execute the pipeline

env.execute()
