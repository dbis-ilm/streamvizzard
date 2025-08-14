from __future__ import annotations

import json
from typing import Optional, Type, Dict, Any

from spe.common.dataType import DataType
from spe.common.serialization.serializationMode import SerializationMode


class Signal:
    class Iterator:
        def __init__(self, data):
            self.index = 0
            self.data = data

        def __next__(self):
            if self.index >= len(self.data):
                raise StopIteration

            result = self.data[self.index]

            self.index += 1

            return result

    def __init__(self, samplingRate: int, data: list):
        self.samplingRate = samplingRate
        self.data = data

    def __iter__(self):
        return Signal.Iterator(self.data)

    def nyq(self) -> float:
        return 0.5 * self.samplingRate

    def toJSON(self) -> Optional[str]:
        return json.dumps({"samplingRate": self.samplingRate, "data": self.data})

    @staticmethod
    def fromJSON(data: str) -> Optional[Signal]:
        d = json.loads(data)

        return Signal(d["samplingRate"], d["data"])


class SignalType(DataType):
    name = "Signal"

    class SignalDTD(DataType.Definition):
        def __init__(self):
            super().__init__(SignalType.name)

            self.registerSerializer(SerializationMode.JSON, lambda sig: sig.toJSON())
            self.registerDeserializer(SerializationMode.JSON, Signal.fromJSON)

        def getValueType(self) -> Optional[Type]:
            return Signal

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            return SignalType(self)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            return SignalType(self)

    def __init__(self, definition: SignalDTD):
        super().__init__(definition, uniform=True)
