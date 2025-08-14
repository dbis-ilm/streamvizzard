import string
import types

from spe.runtime.compiler.codegeneration.frameworks.common import pythonSerialization
from spe.runtime.compiler.codegeneration.frameworks.common.pythonSerialization import encodeJSON, decodeJSON
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkUtils import PyFlinkStruct

# Serialization definitions

pyFlinkSerializationModule: types.ModuleType = pythonSerialization
pyFlinkJSONSerializer = encodeJSON.__name__
pyFlinkJSONDeserializer = decodeJSON.__name__
pyFlinkCustomJSONDeserializerDict = "customJSONDeserializer"

# ----------------------------------------------------------------------------------------------------------------------

# Custom EventTimeAssigner for the watermark strategy.
# Currently, the data is a black box and does not provide real event times so we use epoch + tuple nr as unique order.
# Tuple nr is required for high frequency sources that produces batches of data with same epoch.
# -> Flink is limited to ms EventTime resolution
# However: The Tuple Nr Offset could lead to big jumps in EventTime for high frequency sources
# IngestionTime would lead to same EventTimes across multiple tuples.
# Limitation: This only works for single-node sources since otherwise tuple orders might be mixed up.

pyFlinkEventTimeAssignerDef = PyFlinkStruct("eventTimeAssigner", """
class EventTimeAssigner(TimestampAssigner):
    def __init__(self):
        self.counter = 0

    def extract_timestamp(self, value, record_timestamp: int) -> int:
        self.counter += 1

        return int(time.time() * 1000) + self.counter
""", """
import time
from pyflink.common.watermark_strategy import TimestampAssigner
""")

pyFlinkEventTimeAssigner = "EventTimeAssigner"

# ----------------------------------------------------------------------------------------------------------------------

# Join process function to assign tuples of one input stream to tuples of another stream.

pyFlinkJoinOpDef = PyFlinkStruct("StreamBufferedJoinFunction", """
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
            """, "from pyflink.datastream.functions import CoProcessFunction")

pyFlinkJoinOpAssign = string.Template(".process(StreamBufferedJoinFunction(), output_type=$typeHint)"
                                      ".set_parallelism($parallelism)")

# ----------------------------------------------------------------------------------------------------------------------

# Ordered Join process function to assign tuples of one input stream to tuples of another stream.
# This reorders the incoming tuples of both streams based on event-time and combines them accordingly.

pyFlinkOrderedJoinOpDef = PyFlinkStruct("StreamBufferedOrderedJoinFunction", """
    class StreamBufferedOrderedJoinFunction(KeyedCoProcessFunction):
        def __init__(self, timerInterval):
            self.timerInterval = timerInterval
            self.timerRegistered = False
    
            # heap of (eventTime, tuple)
            self.s1Buffer = []
            self.s2Buffer = []
            
        def process_element1(self, value, ctx: KeyedCoProcessFunction.Context):
            eventTime = ctx.timestamp()
                    
            # Buffer the event
            heapq.heappush(self.s1Buffer, (eventTime, value))

            self.setupTimer(ctx)
            
        def process_element2(self, value, ctx: KeyedCoProcessFunction.Context):
            eventTime = ctx.timestamp()
                    
            # Buffer the event
            heapq.heappush(self.s2Buffer, (eventTime, value))

            self.setupTimer(ctx)

        def setupTimer(self, ctx: KeyedCoProcessFunction.Context):
            # Register a timer if none is registered
            
            if not self.timerRegistered:
                triggerTime = ctx.timer_service().current_watermark() + self.timerInterval
                ctx.timer_service().register_event_time_timer(triggerTime)
                self.timerRegistered = True

        def on_timer(self, timestamp: int, ctx: KeyedCoProcessFunction.OnTimerContext):
            watermark = ctx.timer_service().current_watermark()
    
            # Emit all tuple pairs where eventTime <= watermark
            
            while (self.s1Buffer and self.s2Buffer and
                   self.s1Buffer[0][0] <= watermark and
                   self.s2Buffer[0][0] <= watermark):
                eventTime1, value1 = heapq.heappop(self.s1Buffer)
                eventTime2, value2 = heapq.heappop(self.s2Buffer)
                
                yield value1, value2
    
            # Check if we still have buffered elements and schedule next timer
            
            if self.s1Buffer and self.s2Buffer:
                trigger_time = watermark + self.timerInterval
                ctx.timer_service().register_event_time_timer(trigger_time)
                self.timerRegistered = True
            else:
                # No more elements, clear timer flag
                self.timerRegistered = False
    """, """
    import heapq
    from pyflink.datastream import KeyedCoProcessFunction
    """)

# Reorder join operator assignment to the connected input datastream.
# Partitions the input stream into equal hash groups according to the parallelism of the operator.
# Requires a separate hash function for each connected stream.

pyFlinkOrderedJoinOpAssign = string.Template(".key_by($keyFunc, $keyFunc)"
                                             ".process(StreamBufferedOrderedJoinFunction(env.get_config().get_auto_watermark_interval()), output_type=$typeHint)"
                                             ".set_parallelism($parallelism)")

# ----------------------------------------------------------------------------------------------------------------------

# Reorder operator to restore the event-time tuple order within key-groups.

pyFlinkReorderEventsOpDef = PyFlinkStruct("ReorderEventsFunction", """
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
    """, """
    import heapq
    from pyflink.datastream import KeyedProcessFunction
    """)

# Reorder operator assignment to the input datastream.
# Partitions the input stream into equal hash groups according to the parallelism of the operator.

pyFlinkReorderEventsOpAssign = string.Template(".key_by($keyFunc)"
                                               ".process(ReorderEventsFunction(env.get_config().get_auto_watermark_interval()), output_type=$typeHint)"
                                               ".set_parallelism($parallelism)")

# ----------------------------------------------------------------------------------------------------------------------

# Rate Limiter, primarily designed for bounded sources (e.g. TextFile) to reduce the incoming data rate.

pyFlinkRateLimiterOpName = "RateLimiter"

pyFlinkRateLimiterOpDef = PyFlinkStruct("RateLimiter", """
    class RateLimiter(MapFunction):
        def __init__(self, targetRate: float):
            self.sleepTime = 1.0 / targetRate
            self.startTime = None
            self.tupCounter = 0
    
        def map(self, value):
            current = timeit.default_timer()
    
            if self.startTime is None:
                self.startTime = current
    
            # Compensates inaccuracies in sleeps by fixed produce 'clock'
            nextProduce = self.startTime + self.tupCounter * self.sleepTime
    
            targetSleep = nextProduce - current
    
            if targetSleep > 1e-3:
                time.sleep(targetSleep)
    
            self.tupCounter += 1
    
            return value""", """
            from pyflink.datastream.functions import MapFunction
            import timeit
            import time""")
