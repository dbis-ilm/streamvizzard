import json
import time

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.source import Source
from spe.common.timer import Timer


class VideoFile(Source):
    def __init__(self,  opID: int):
        super(VideoFile, self).__init__(opID, 0, 1)

        self.videoCapture = None

        self.path = ""
        self.repeat = False
        self.limitRate = False
        self.frameRate = 0

    def setData(self, data: json):
        self.path = data["path"]
        self.repeat = data["repeat"]
        self.frameRate = data["frameRate"]
        self.limitRate = data["limitRate"]

    def getData(self) -> dict:
        return {"path": self.path, "repeat": self.repeat, "frameRate": self.frameRate, "limitRate": self.limitRate}

    def onRuntimeDestroy(self):
        super(VideoFile, self).onRuntimeDestroy()

        if self.videoCapture is not None and self.videoCapture.isOpened:
            self.videoCapture.release()

    def _runSource(self):
        lastPath = self.path

        # Interactive mode -> we can reopen file if path changed

        while self.isRunning():
            # Skip if nothing changed and we shall not repeat video
            if self.videoCapture is not None and not self.repeat\
                    and lastPath == self.path:
                time.sleep(0.25)

                continue

            # Try to load the video
            try:
                self.videoCapture = cv2.VideoCapture(self.path)
                lastPath = self.path
            except Exception:
                self.onExecutionError()

                time.sleep(0.25)

                continue

            # Stream video
            while self.isRunning() and self.videoCapture.isOpened():
                # Video source changed
                if self.path != lastPath:
                    self.videoCapture.release()

                    break

                # Read has quite some delay since it loads and decodes the image.
                # Maybe could be improved by moving the read function to a different thread + frame queue
                startTime = Timer.currentTime()
                ret, frame = self.videoCapture.read()
                endTime = Timer.currentTime()

                if not ret:
                    self.videoCapture.release()

                    if self.repeat:
                        self.videoCapture = cv2.VideoCapture(self.path)
                else:
                    self._produce((Image(frame),))

                # This will actually take a little more time than the desired rate because of windows tick rate
                # On Windows system sometimes the tick rate is around 13ms which differs a lot from the desired rate

                if self.limitRate:
                    sleepTime = max(0, (1.0 / self.frameRate) - (endTime - startTime))

                    if sleepTime > 1e-3:
                        time.sleep(sleepTime)
