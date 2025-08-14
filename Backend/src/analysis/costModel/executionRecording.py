from __future__ import annotations
import json
from json import JSONEncoder, JSONDecoder
from typing import List, TYPE_CHECKING

from analysis.costModel.costModel import CostModelTarget

if TYPE_CHECKING:
    from analysis.costModel.costModel import CostModelEnv, CostModelMetaData


class ExecutionRecording:
    """ Recordings are execution-environment specific, while targets calculate models based on the recordings. """

    def __init__(self, env: CostModelEnv, entries: List[Entry]):
        self.env = env
        self.entries = entries

    class Entry:
        """ Reflects recorded results of an execution of an operator. """

        def __init__(self, inputSize: float, params: List[RecordingParam],
                     outputSize: float, executionTime: float):
            self.params = params
            self.inputSize = inputSize  # Size in bytes
            self.executionTime = executionTime  # Time in s
            self.outputSize = outputSize  # Size in bytes

        def getTargetValue(self, target: CostModelTarget):
            if target == CostModelTarget.EXECUTION_TIME:
                return self.executionTime
            elif target == CostModelTarget.OUTPUT_SIZE:
                return self.outputSize

            return None

        def getParam(self, name: str):
            for p in self.params:
                if p.name == name:
                    return p
            return None

        def getValue(self, name: str):
            p = self.getParam(name)
            return p.value if p is not None else None

        def toJSON(self):
            return json.dumps({"executionTime": self.executionTime, "outputSize": self.outputSize,
                               "params": self.params, "inputSize": self.inputSize}, cls=RecordingParamEncoder)

        @staticmethod
        def fromJSON(data: str):
            j = json.loads(data, cls=RecordingParamDecoder)

            return ExecutionRecording.Entry(j["inputSize"], j["params"], j["outputSize"], j["executionTime"])


class RecordingParam:
    def __init__(self, name: str, value):
        self.name = name
        self.value = value

    @staticmethod
    def getMetaDataParams(metaData: CostModelMetaData) -> List[RecordingParam]:
        return [RecordingParam(k.value, v) for k, v in metaData.metaData.items()]


class RecordingParamEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class RecordingParamDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    @staticmethod
    def object_hook(dct):
        if "name" in dct:
            return RecordingParam(dct["name"], dct["value"])

        return dct
