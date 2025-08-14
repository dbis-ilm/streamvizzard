"""
|--------------------------------------------------------|
| This code was generated automatically by StreamVizzard.|
|--------------------------------------------------------|
"""

from __future__ import annotations
import json
import time
import numpy
import heapq
import pandas
import timeit
import statistics
from typing import Dict
from typing import Callable
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

            yield value

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


kafkaSource_KafkaSource_1128 = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9093") \
    .set_group_id("my-group") \
    .set_topics("my-topic") \
    .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
    .set_value_only_deserializer(SimpleStringSchema("utf-8")) \
    .build()


def map_ParseJSON_990(inTuple):
    return decodeJSON(inTuple)


def map_UDF_992(inTuple):
    return (inTuple['prices'],)[0]


def map_MissingValues_1062(inTuple):
    data = inTuple
    dataSeries = pandas.Series([numpy.nan if v is None else v for v in data])
    if 'linear' == 'linear':
        df = dataSeries.interpolate(limit_direction='both')
    elif 'linear' == 'polynomial':
        df = dataSeries.interpolate(
            method='polynomial', order=3, limit_direction='both')
    elif 'linear' == 'pad':
        df = dataSeries.interpolate(
            method='pad', limit=len(data), limit_direction='both')
    else:
        df = dataSeries
        df.dropna(inplace=True)
    data_frame = pandas.DataFrame(df, columns=['data'])
    data_cleaned = list(data_frame.itertuples(index=True, name=None))
    data_cleaned_list = [t[1] for t in data_cleaned]
    return (data_cleaned_list,)[0]


def map_AnomalyDetection_991(inTuple):
    data = inTuple
    Q3, Q1 = numpy.percentile(data, [75, 25])
    IQR = Q3 - Q1
    lower_limit = Q1 - 1.5 * IQR
    upper_limit = Q3 + 1.5 * IQR
    data_cleaned = []
    data_outlier = []
    fallbackVal = statistics.median(data)
    for i, value in enumerate(data):
        if value < lower_limit or value > upper_limit:
            data_outlier.append(value)
            start = max(0, i - 25)
            end = min(len(data), i + 25 + 1)
            neighbors = [data[j] for j in range(start, end) if j != i]
            if neighbors:
                if 'mean' == 'mean':
                    replacement = statistics.mean(neighbors)
                elif 'mean' == 'median':
                    replacement = statistics.median(neighbors)
                elif 'mean' == 'mode':
                    try:
                        replacement = statistics.mode(neighbors)
                    except statistics.StatisticsError:
                        replacement = fallbackVal
                else:
                    replacement = fallbackVal
            else:
                replacement = fallbackVal
            data_cleaned.append(replacement)
        else:
            data_outlier.append(None)
            data_cleaned.append(value)
    return (data_cleaned, data_outlier)


def map_UDF_994(inTuple):
    prices = inTuple[0]
    median = statistics.median(prices)
    avg = statistics.mean(prices)
    stdDev = statistics.stdev(prices)
    res = {'median': median, 'avg': avg, 'stdDev': stdDev}
    return ((median, timeit.default_timer()),)[0]


fs_FileSink_686 = FileSink \
    .for_row_format("/home/pyflink", Encoder.simple_string_encoder()) \
    .with_output_file_config(OutputFileConfig.builder().with_part_prefix("energyOut").with_part_suffix(".txt").build()) \
    .build()


# ---------------- Pipeline Construction -----------------

KafkaSource_1128 = env.from_source(kafkaSource_KafkaSource_1128, WatermarkStrategy.for_monotonous_timestamps(), 'kafkaSource_KafkaSource_1128', type_info=Types.STRING()).set_parallelism(1).assign_timestamps_and_watermarks(WatermarkStrategy.for_monotonous_timestamps().with_idleness(Duration.of_seconds(10)).with_timestamp_assigner(EventTimeAssigner())).set_parallelism(1)
ParseJSON_990 = KafkaSource_1128.map(map_ParseJSON_990).set_parallelism(5)
UDF_992 = ParseJSON_990.map(map_UDF_992).set_parallelism(5)
MissingValues_1062 = UDF_992.map(map_MissingValues_1062, output_type=Types.LIST(Types.DOUBLE())).set_parallelism(5)
AnomalyDetection_991 = MissingValues_1062.map(map_AnomalyDetection_991, output_type=Types.TUPLE([Types.LIST(Types.DOUBLE()), Types.PICKLED_BYTE_ARRAY()])).set_parallelism(5)
UDF_994 = AnomalyDetection_991.key_by(lambda x: 1).process(ReorderEventsFunction(env.get_config().get_auto_watermark_interval()), output_type=Types.LIST(Types.DOUBLE())).set_parallelism(1).map(map_UDF_994, output_type=Types.TUPLE([Types.DOUBLE(), Types.DOUBLE()])).set_parallelism(1)
FileSink_686 = UDF_994.sink_to(fs_FileSink_686).set_parallelism(1)

# Execute the pipeline

env.execute()

