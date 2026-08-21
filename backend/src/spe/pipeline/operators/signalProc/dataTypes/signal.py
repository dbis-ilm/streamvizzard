from __future__ import annotations

import json
import math
import sys
from typing import Optional, Type, Dict, Any

import numpy as np
import numpy.typing as npt
from scipy import signal

from spe.common.dataType import DataType
from spe.common.serialization.serializationMode import SerializationMode


class Signal:
    """
    Signals are representing multichannel audio in an interleaved 1D format.
    Sample: Single audio value representing the signal amplitude for one channel
    Frame: Collection of samples from all channels
    """

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

    def __init__(self, samplingRate: int, data: npt.NDArray[np.float64]):
        self.samplingRate = samplingRate
        self.data = data

    def __iter__(self):
        return Signal.Iterator(self.data)

    @property
    def channels(self):
        return self.data.shape[1]

    @property
    def samples(self):
        return self.data.shape[0]

    def getDataSize(self):
        return sys.getsizeof(self.samplingRate) + sys.getsizeof(self.channels) + self.data.nbytes

    def nyq(self) -> float:
        return 0.5 * self.samplingRate

    def toJSON(self) -> Optional[str]:
        return json.dumps({"samplingRate": self.samplingRate, "channels": self.channels, "data": self.data.tolist()})

    @staticmethod
    def fromJSON(data: str) -> Optional[Signal]:
        d = json.loads(data)

        return Signal(d["samplingRate"], np.array(d["data"], dtype=np.int16))

    def getResampled(self, newSampleRate: int, mode: int) -> Signal:
        """Return resampled signal using different modes.

        Args:
            newSampleRate: Target sampling rate in Hz.
            mode:
                Resampling mode identifier.

                0 = resample : FFT-based, ensures exact sample size, may produce aliasing

                1 = resample_poly : Polyphase FIR filtering, good antialiasing

                2 = decimate : Anti-alias filter + downsampling
        """

        n = len(self.data)

        if mode == 0:
            data = signal.resample(self.data, newSampleRate, axis=0)
        elif mode == 1:
            g = math.gcd(n, newSampleRate)
            up = newSampleRate // g
            down = n // g

            data = signal.resample_poly(self.data, up, down, axis=0)
        elif mode == 2:
            if n <= newSampleRate:
                data = self.data.copy()
            else:
                q = int(n / newSampleRate)
                data = signal.decimate(self.data, q, axis=0)
        else:
            raise ValueError("Invalid mode param!")

        return Signal(newSampleRate, data)


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

    def __init__(self, definition: Optional[SignalDTD] = None):
        if definition is None:
            definition = DataType.getDefinitionByName(SignalType.name)

        super().__init__(definition, uniform=True)


DataType.register(SignalType.SignalDTD())
