import time
from pathlib import Path
from typing import Optional, Dict

import wave

import numpy as np

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal
from spe.pipeline.operators.source import Source


class AudioFile(Source):
    def __init__(self,  opID: int):
        super(AudioFile, self).__init__(opID, 0, 1)

        self._wfFile: Optional[wave.Wave_read] = None

        self.repeat = False
        self.rate = 0  # Hz
        self.chunkSize = 1024
        self.path = ""

    def getData(self) -> dict:
        return {"rate": self.rate, "path": self.path, "repeat": self.repeat, "chunkSize": self.chunkSize}

    def setData(self, data: Dict):
        self.rate = int(data["rate"])
        self.chunkSize = int(data["chunkSize"])
        self.path = data["path"]
        self.repeat = data["repeat"]

    def onRuntimeDestroy(self):
        super(AudioFile, self).onRuntimeDestroy()

        self._closeFile()

    def _openFile(self):
        self._closeFile()

        if len(self.path.strip()) == 0:
            self.onExecutionError("Empty file path!")

            return

        path = Path(self.path)

        if path.suffix != ".wav":
            self.onExecutionError("Unsupported audio format! Only supports: .wav")

            return

        try:
            self._wfFile = wave.open(self.path, 'rb')
        except Exception:
            self.onExecutionError()

    def _closeFile(self):
        if self._wfFile is not None:
            self._wfFile.close()

            self._wfFile = None

    def _runSource(self):
        completed = False

        while self.isRunning():
            if completed and not self.repeat:  # To allow dynamic enable / disable of repeat
                time.sleep(0.25)

                continue

            try:
                currentPath = self.path

                self._openFile()

                if self._wfFile is None:
                    time.sleep(0.25)  # Avoid infinity loop for trying to load invalid paths

                    continue

                completed = False

                while self.isRunning():
                    if currentPath != self.path:
                        break

                    # Data size = channelCount * chunkSize(frameCount)
                    data = self._wfFile.readframes(self.chunkSize)

                    if not data:  # End of file
                        completed = True

                        break

                    # Unpack data as a  16 - bit [results interleaved 1D layout] and reshape to (samples, channels)
                    dataArray = np.frombuffer(data, dtype=np.int16) / 32768.0  # Scale to [-1,1] (int16 storage)
                    dataArray = dataArray.reshape(-1, self._wfFile.getnchannels()).astype(np.float64)

                    self._produce((Signal(self.rate, dataArray),))

                    sleepDuration = self.chunkSize / self.rate

                    if sleepDuration > 1e-3:
                        time.sleep(sleepDuration)
            except Exception:
                self.onExecutionError()
