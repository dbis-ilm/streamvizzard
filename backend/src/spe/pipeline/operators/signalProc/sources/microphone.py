from typing import Optional, Dict

import numpy as np
import pyaudio

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal
from spe.pipeline.operators.source import Source


class Microphone(Source):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    def __init__(self,  opID: int):
        super(Microphone, self).__init__(opID, 0, 1)

        self._audioCapture: Optional[pyaudio.PyAudio] = None
        self._audioStream: Optional[pyaudio.Stream] = None

        self.rate = 0
        self.chunkSize = 1024

    def getData(self) -> dict:
        return {"rate": self.rate, "chunkSize": self.chunkSize}

    def setData(self, data: Dict):
        newRate = int(data["rate"])
        newChunkSize = int(data["chunkSize"])

        # Might crash if to frequent updates!
        if self.rate != newRate or self.chunkSize != newChunkSize:
            self.rate = newRate
            self.chunkSize = newChunkSize

            self._closeAudioStream()

    def _ensureAudioSource(self):
        if self._audioCapture is None:
            self._audioCapture = pyaudio.PyAudio()

        if self._audioStream is None:
            # Open new stream
            self._audioStream = self._audioCapture.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunkSize
            )

    def _closeAudioStream(self):
        if self._audioStream is not None:
            s = self._audioStream
            self._audioStream = None  # Avoid reading while we close stream

            s.stop_stream()
            s.close()

    def onRuntimeDestroy(self):
        super(Microphone, self).onRuntimeDestroy()

        self._closeAudioStream()

        if self._audioCapture is not None:
            self._audioCapture.terminate()

            self._audioCapture = None

    def _runSource(self):
        while self.isRunning():
            self._ensureAudioSource()

            if self._audioStream is not None:
                try:
                    data = self._audioStream.read(self.chunkSize, exception_on_overflow=False)

                    # Unpack data as a  16 - bit [results interleaved 1D layout] and reshape to (samples, channels)
                    dataArray = np.frombuffer(data, dtype=np.int16) / 32768.0  # Scale to [-1,1] (int16 storage)
                    dataArray = dataArray.reshape(-1, self.CHANNELS).astype(np.float64)

                    self._produce((Signal(self.rate, dataArray),))
                except Exception:
                    self.onExecutionError()
