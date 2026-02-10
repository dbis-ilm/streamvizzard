from __future__ import annotations
import json
import time
import numpy
import heapq
import pandas
import timeit
import statistics
from pyflink.common import Types
from pyflink.common import Encoder
from pyflink.common import Duration
from pyflink.common import Configuration
from pyflink.common import WatermarkStrategy
from pyflink.datastream import KeyedProcessFunction
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import TimestampAssigner
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


class ReorderEventsFunction(KeyedProcessFunction):
    # Reorders all incoming events base on the provided timestamp (EventTime)

    def __init__(self, timerInterval):
        self.timerInterval = timerInterval
        self.timerRegistered = False

        self.buffer = []  # heap of (eventTime, tuple)

    def process_element(self, value, ctx: KeyedProcessFunction.Context):
        eventTime = ctx.timestamp()

        # Buffer the event
        heapq.heappush(self.buffer, (eventTime, value))

        # Register a timer if none is registered
        if not self.timerRegistered:
            triggerTime = ctx.timer_service().current_watermark() + self.timerInterval
            ctx.timer_service().register_event_time_timer(triggerTime)
            self.timerRegistered = True

    def on_timer(self, timestamp: int, ctx: KeyedProcessFunction.OnTimerContext):
        watermark = ctx.timer_service().current_watermark()

        # Emit all events whose eventTime <= watermark
        while self.buffer and self.buffer[0][0] <= watermark:
            eventTime, value = heapq.heappop(self.buffer)

            yield value, timeit.default_timer()

        # Check if we still have buffered elements
        if self.buffer:
            # Schedule next timer
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


# ---------------------- Operators -----------------------

kafkaSourceDef = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


def resolveAnomalies(inTuple):
    prices = json.loads(inTuple)["prices"]

    # Missing Val

    dataSeries = pandas.Series([numpy.nan if v is None else v for v in prices])
    df = dataSeries.interpolate(limit_direction='both')
    data_frame = pandas.DataFrame(df, columns=['data'])
    data_cleaned = list(data_frame.itertuples(index=True, name=None))
    data_cleaned_list = [t[1] for t in data_cleaned]

    # Anomalies

    Q3, Q1 = numpy.percentile(data_cleaned_list, [75, 25])
    IQR = Q3 - Q1
    lower_limit = Q1 - 1.5 * IQR
    upper_limit = Q3 + 1.5 * IQR
    data_cleaned = []
    fallbackVal = statistics.median(data_cleaned_list)

    for i, value in enumerate(data_cleaned_list):
        if value < lower_limit or value > upper_limit:
            start = max(0, i - 25)
            end = min(len(data_cleaned_list), i + 25 + 1)
            neighbors = [data_cleaned_list[j] for j in range(start, end) if j != i]
            if neighbors:
                replacement = statistics.mean(neighbors)
            else:
                replacement = fallbackVal
            data_cleaned.append(replacement)
        else:
            data_cleaned.append(value)
    return statistics.median(data_cleaned)


fsDef = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("energyOut").with_part_suffix(".txt").build()) \
    .build()


# ---------------- Pipeline Construction -----------------

KafkaSource = env.from_source(kafkaSourceDef, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource', type_info=Types.STRING()).set_parallelism(1).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10)).with_timestamp_assigner(EventTimeAssigner())).set_parallelism(1)
AnomalyResolver = KafkaSource.map(resolveAnomalies, output_type=Types.DOUBLE()).set_parallelism(5)
Reorder = AnomalyResolver.key_by(lambda x: 1).process(ReorderEventsFunction(env.get_config().get_auto_watermark_interval()), output_type=Types.TUPLE([Types.DOUBLE(), Types.DOUBLE()])).set_parallelism(1)
FileSink = Reorder.sink_to(fsDef).set_parallelism(1)

env.execute()
