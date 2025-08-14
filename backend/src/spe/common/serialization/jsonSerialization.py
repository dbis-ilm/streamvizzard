import json
import logging
import traceback

from spe.common.dataType import DataType
from spe.common.serialization.serializationMode import SerializationMode


def serializeToJSON(data):
    return json.dumps(data, default=jsonDefaultEncoder)


def jsonDefaultEncoder(data):
    dtDef = DataType.retrieveDefinition(data)

    if dtDef is not None:
        encoder = dtDef.getSerializer(SerializationMode.JSON)

        if encoder is not None:
            try:
                return _customTypeResult(dtDef.getValueTypeName(), encoder(data))
            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())

    type_name = data.__class__.__name__

    raise TypeError(f"Object of type {type_name} is not serializable")


def _customTypeResult(typeName: str, serializedData):
    return {"type": typeName, "data": serializedData}


def deserializeFromJSON(data: str):
    return json.loads(data, object_hook=jsonDefaultDecoder)


def jsonDefaultDecoder(data):
    if "type" not in data:
        return data  # No custom object

    dtDef = DataType.getDefinitionByValueTypeName(data["type"])
    dataVal = data["data"]

    if dtDef is not None:
        decoder = dtDef.getDeserializer(SerializationMode.JSON)

        if decoder is not None:
            try:
                return decoder(dataVal)
            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())

    return dataVal  # Fallback
