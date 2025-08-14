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
