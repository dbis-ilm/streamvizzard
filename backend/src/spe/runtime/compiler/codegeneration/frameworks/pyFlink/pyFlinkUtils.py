import textwrap
from enum import Enum
from typing import Optional

from spe.common.dataType import DataType, BooleanType, StringType, FloatType, IntegerType, BytesType, TupleType, \
    ArrayType, WindowType, DictType, NoneType
from spe.pipeline.operators.imageProc.dataTypes.image import ImageType
from spe.pipeline.operators.signalProc.dataTypes.signal import SignalType
from utils.utils import printWarning


class PyFlinkStruct:
    def __init__(self, name: str, funcCode: str, imports: Optional[str]):
        self.name = name
        self.funcCode = textwrap.dedent(funcCode)
        self.imports = textwrap.dedent(imports) if imports is not None else None


class PyFlinkTags(Enum):
    SOURCE_BOUNDED = 1
    SOURCE_UNBOUNDED = 2


class PyFlinkJARs(Enum):
    FLINK_KAFKA_CONNECTOR = ("flink-sql-connector-kafka.jar", "https://mvnrepository.com/artifact/org.apache.flink/flink-sql-connector-kafka")


# https://nightlies.apache.org/flink/flink-docs-master/docs/dev/python/datastream/data_types/
# https://nightlies.apache.org/flink/flink-docs-master/api/python/reference/pyflink.common/typeinfo.html

def getPyFlinkTypeFor(dt: Optional[DataType]) -> Optional[str]:
    if dt is None:
        return None

    if isinstance(dt, NoneType):
        return None
    if isinstance(dt, BooleanType):
        return "Types.BOOLEAN()"
    elif isinstance(dt, StringType):
        return "Types.STRING()"
    elif isinstance(dt, FloatType):
        return "Types.DOUBLE()"
    elif isinstance(dt, IntegerType):
        return "Types.INT()"
    elif isinstance(dt, ImageType):
        return "Types.PICKLED_BYTE_ARRAY()"
    elif isinstance(dt, SignalType):
        return "Types.PICKLED_BYTE_ARRAY()"
    elif isinstance(dt, BytesType):
        return "Types.PRIMITIVE_ARRAY(Types.BYTE())"
    elif isinstance(dt, TupleType):
        fieldTypes = []

        for childType in dt.entryTypes:
            t = getPyFlinkTypeFor(childType)

            if t is None:  # Missing subTypes not supported
                return None

            fieldTypes.append(t)

        return f"Types.TUPLE([{', '.join(fieldTypes)}])"
    elif isinstance(dt, ArrayType):
        elementType = getPyFlinkTypeFor(dt.entryType)

        if elementType is None:  # Missing subTypes not supported
            return None

        return f"Types.LIST({elementType})"
    elif isinstance(dt, WindowType):
        elementType = getPyFlinkTypeFor(dt.entryType)

        if elementType is None:  # Missing subTypes not supported
            return None

        return f"Types.LIST({elementType})"
    elif isinstance(dt, DictType):
        if not dt.uniform:  # If we can't verify that key, val are uniform we need to pickle it (unchecked => not uniform)
            return "Types.PICKLED_BYTE_ARRAY()"

        keyType = getPyFlinkTypeFor(dt.keyType)
        valType = getPyFlinkTypeFor(dt.valType)

        # Missing subTypes not supported

        if keyType is None or valType is None:
            return None

        # Key, Val only supports primitive types

        if not dt.keyType.definition.primitive or dt.valType.definition.primitive:
            return None

        return f"Types.MAP({keyType}, {valType})"

    printWarning(f"Unsupported type {dt.typeName} for retrieving compatible PyFlink type!")

    return None


def getUniformKeyBySet(para: int) -> list[int]:
    # Simulates Flink's hashing function to calculate keys that are evenly distributed across the desired executors
    # Flink hashes the provided key (.key_by) using its own hash function to determine the assigned subTask

    # Verified overrides

    if para == 1:
        return [0]
    elif para == 2:
        return [0, 2]
    elif para == 3:
        return [0, 1, 2]
    elif para == 4:
        return [0, 2, 4, 8]
    elif para == 5:
        return [0, 5, 21, 14, 17]
    elif para == 6:
        return [0, 1, 2, 4, 6, 8]
    elif para == 7:
        return [0, 1, 2, 4, 6, 8, 14]
    elif para == 8:
        return [0, 2, 4, 6, 8, 19, 22]
    elif para == 9:
        return [0, 1, 2, 3, 4, 6, 8, 14, 19]
    elif para == 10:
        return [0, 1, 2, 4, 6, 8, 14, 17, 19, 22]

    # Fallback

    def flinkMurmurHash(code: int) -> int:
        code &= 0xFFFFFFFF
        code = (code * 0xcc9e2d51) & 0xFFFFFFFF
        code = ((code << 15) | (code >> 17)) & 0xFFFFFFFF
        code = (code * 0x1b873593) & 0xFFFFFFFF
        code = ((code << 13) | (code >> 19)) & 0xFFFFFFFF
        code = (code * 5 + 0xe6546b64) & 0xFFFFFFFF
        code ^= 4  # length in bytes for one int
        code ^= (code >> 16)
        code = (code * 0x85ebca6b) & 0xFFFFFFFF
        code ^= (code >> 13)
        code = (code * 0xc2b2ae35) & 0xFFFFFFFF
        code ^= (code >> 16)
        return code

    def subtaskForKey(key: int, maxPara: int = 128) -> int:
        key_group = (flinkMurmurHash(key) & 0x7fffffff) % maxPara
        return (key_group * para) // maxPara

    keys = [-1] * para

    for sub in range(para):
        for k in range(10_000):
            if subtaskForKey(k, para) == sub:
                keys[sub] = k
                break

    return keys
