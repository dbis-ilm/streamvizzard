import json
import time

import cv2

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.source import Source


class WebCam(Source):
    def __init__(self,  opID: int):
        super(WebCam, self).__init__(opID, 0, 1)

        self.videoCapture = None

        self.frameRate = 0
        self.device = 0

    def setData(self, data: json):
        self.frameRate = int(data["frameRate"])

        if data["device"] != self.device:
            if self.videoCapture is not None:
                self.videoCapture.release()
            self.videoCapture = None

            self.device = data["device"]

    def getData(self) -> dict:
        return {"frameRate": self.frameRate, "device": self.device}

    def onRuntimeDestroy(self):
        super(WebCam, self).onRuntimeDestroy()

        if self.videoCapture is not None and self.videoCapture.isOpened:
            self.videoCapture.release()

    def _runSource(self):
        while self.isRunning():
            # Try to open the webcam
            if self.videoCapture is None:
                try:
                    self.videoCapture = cv2.VideoCapture(self.device)
                except Exception:
                    self.onExecutionError()

                    time.sleep(0.25)

                    continue

            # Stream video
            while self.isRunning() and self.videoCapture is not None and self.videoCapture.isOpened():
                # Read has quite some delay since it loads and decodes the image.
                # Maybe could be improved by moving the read function to a different thread + frame queue
                ret, frame = self.videoCapture.read()

                if not ret:
                    self.videoCapture.release()
                    self.videoCapture = None

                    break
                else:
                    self._produce((Image(frame),))

                if 0 < self.frameRate < 100:
                    # This will actually take a little more time than the desired rate because of windows tick rate
                    # On Windows system sometimes the tick rate is around 13ms which differs a lot from the desired rate

                    time.sleep(1 / self.frameRate)
