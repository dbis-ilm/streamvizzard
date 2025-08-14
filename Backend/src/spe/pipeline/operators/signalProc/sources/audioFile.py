import asyncio
import json
import time
from array import array
from pathlib import Path
from typing import Optional

import wave

from spe.pipeline.operators.signalProc.dataTypes.signal import Signal
from spe.pipeline.operators.source import Source


class AudioFile(Source):
    CHUNK_SIZE = 1024

    def __init__(self,  opID: int):
        super(AudioFile, self).__init__(opID, 0, 1)

        self._wfFile: Optional[wave.Wave_read] = None

        self.repeat = False
        self.rate = 0  # Hz
        self.chunkSize = 1024
        self.path = ""

    def getData(self) -> dict:
        return {"rate": self.rate, "path": self.path, "repeat": self.repeat}

    def setData(self, data: json):
        self.rate = int(data["rate"])
        self.path = data["path"]
        self.repeat = data["repeat"]

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        super(AudioFile, self).onRuntimeCreate(eventLoop)

        path = Path(self.path)

        if path.suffix != ".wav":
            self.onExecutionError("Unsupported audio format! Only supports: .wav")

            return

        try:
            self._wfFile = wave.open(self.path, 'rb')
        except Exception:
            self.onExecutionError()

    def onRuntimeDestroy(self):
        super(AudioFile, self).onRuntimeDestroy()

        if self._wfFile is not None:
            self._wfFile.close()

            self._wfFile = None

    def _runSource(self):
        closed = False

        while self.isRunning():
            if self._wfFile is not None:
                if closed and not self.repeat:  # To allow dynamic enable / disable of repeat
                    time.sleep(0.25)

                    continue

                closed = False

                try:
                    data = self._wfFile.readframes(self.CHUNK_SIZE)

                    if not data:  # End of file
                        closed = True

                        self._wfFile.rewind()

                        continue

                    # Unpack data as a  16 - bit
                    sampleData = array('h', data)

                    self._produce((Signal(self.rate, list(sampleData)),))

                    sleepDuration = self.CHUNK_SIZE / self.rate

                    if sleepDuration > 1e-3:
                        time.sleep(1 / self.rate)

                except Exception:
                    self.onExecutionError()
