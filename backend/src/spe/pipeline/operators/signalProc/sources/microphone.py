import json
from array import array
from typing import Optional

import pyaudio

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal
from spe.pipeline.operators.source import Source


class Microphone(Source):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    CHUNK = 1024

    def __init__(self,  opID: int):
        super(Microphone, self).__init__(opID, 0, 1)

        self._audioCapture: Optional[pyaudio.PyAudio] = None
        self._audioStream: Optional[pyaudio.Stream] = None

        self.rate = 0

    def getData(self) -> dict:
        return {"rate": self.rate}

    def setData(self, data: json):
        newRate = int(data["rate"])

        # Might crash if to frequent updates!
        if self.rate != newRate:
            self.rate = newRate

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
                frames_per_buffer=self.CHUNK
            )

    def _closeAudioStream(self):
        if self._audioStream is not None:
            self._audioStream.stop_stream()
            self._audioStream.close()

            self._audioStream = None

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
                    data = self._audioStream.read(self.CHUNK, exception_on_overflow=False)

                    # Unpack data as a  16 - bit
                    sample_data = array('h', data)

                    dataArray = list(sample_data)

                    self._produce((Signal(self.rate, dataArray),))
                except Exception:
                    self.onExecutionError()
