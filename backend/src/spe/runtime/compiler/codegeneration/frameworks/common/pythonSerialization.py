import json
from typing import Dict, Callable


# ------------------ Serialization ------------------

customJSONDeserializer: Dict[str, Callable] = dict()


def encodeJSON(data):
    return json.dumps(data, default=jsonSerializer)


def jsonSerializer(data):
    if hasattr(data, "toJSON"):
        return {"type": type(data).__name__, "data": data.toJSON()}

    return data


def decodeJSON(data: str):
    return json.loads(data, object_hook=jsonDeserializer)


def jsonDeserializer(data):
    if "type" not in data:
        return data

    dataType = data["type"]
    dataVal = data["data"]

    des = customJSONDeserializer.get(dataType, None)

    if des is not None:
        return des(dataVal)

    return dataVal

# --------------------------------------------------
