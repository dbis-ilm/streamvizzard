import base64
import logging
import math
import traceback

import cv2

from spe.pipeline.operators.base.dataTypes.scatterplotD import ScatterplotD
from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.imageProc.operators.math.imgBlend import ImgBlend
from spe.pipeline.operators.imageProc.operators.process.canny import Canny
from spe.pipeline.operators.imageProc.operators.process.findContours import FindContours
from spe.pipeline.operators.imageProc.operators.transform.convert import Convert
from spe.pipeline.operators.imageProc.operators.process.eqHistogram import EqHistogram
from spe.pipeline.operators.imageProc.operators.process.gaussianBlur import GaussianBlur
from spe.pipeline.operators.imageProc.operators.math.imgAdd import ImgAdd
from spe.pipeline.operators.imageProc.operators.transform.extractROI import ExtractROI
from spe.pipeline.operators.imageProc.operators.transform.imgLoad import ImgLoad
from spe.pipeline.operators.imageProc.operators.transform.imgMerge import ImgMerge
from spe.pipeline.operators.imageProc.operators.math.imgMultiply import ImgMultiply
from spe.pipeline.operators.imageProc.operators.transform.imgSplit import ImgSplit
from spe.pipeline.operators.imageProc.operators.process.threshold import Threshold
from spe.pipeline.operators.imageProc.operators.transform.imgResize import ImgResize
from spe.pipeline.operators.imageProc.sources.videofile import VideoFile
from spe.pipeline.operators.imageProc.sources.webcam import WebCam
from spe.pipeline.operators.module import Module, MonitorDataType


class ImageProcModule(Module):
    def __init__(self):
        super(ImageProcModule, self).__init__("ImageProc")

    def initialize(self):
        self.registerOp(VideoFile, "Sources/VideoFile")
        self.registerOp(WebCam, "Sources/WebCam")

        self.registerOp(Threshold, "Operators/Process/Threshold")
        self.registerOp(Convert, "Operators/Transform/Convert")
        self.registerOp(EqHistogram, "Operators/Process/EqHistogram")
        self.registerOp(ImgSplit, "Operators/Transform/ImgSplit")
        self.registerOp(ExtractROI, "Operators/Transform/ExtractROI")
        self.registerOp(GaussianBlur, "Operators/Process/GaussianBlur")
        self.registerOp(ImgMultiply, "Operators/Math/ImgMultiply")
        self.registerOp(ImgAdd, "Operators/Math/ImgAdd")
        self.registerOp(ImgBlend, "Operators/Math/ImgBlend")
        self.registerOp(ImgMerge, "Operators/Transform/ImgMerge")
        self.registerOp(ImgResize, "Operators/Transform/ImgResize")
        self.registerOp(Canny, "Operators/Process/Canny")
        self.registerOp(FindContours, "Operators/Process/FindContours")

        self.registerOp(ImgLoad, "Operators/Transform/ImgLoad")

        imgDT = MonitorDataType("IMAGE", lambda x: isinstance(x, Image))
        imgDT.registerDisplayMode(0, self.displayImageRaw)  # Raw
        imgDT.registerDisplayMode(1, self.displayImageGrayscale)  # Grayscale
        imgDT.registerDisplayMode(2, self.displayImageHistogram)  # Histogram
        self.registerMonitorDataType(imgDT)
        self.registerJSONEncoder(Image, self.imgToJson)

        imgArrayDT = MonitorDataType("ARRAY_IMG", lambda x: MonitorDataType.isArrayOf(x, Image))
        imgArrayDT.registerDisplayMode(0, lambda x, y: len(x))  # Count
        imgArrayDT.registerDisplayMode(1, self.displayImgArrayDelta)  # Delta
        imgArrayDT.registerDisplayMode(2, self.displayImgArraySum)  # Sum
        self.registerMonitorDataType(imgArrayDT)

        # Transform Image Window to Image Array
        imgWindowDT = MonitorDataType("WINDOW_IMG", lambda x: MonitorDataType.isWindowOf(x, Image))
        imgWindowDT.registerTransformFunc(lambda x: x.toDataArray())
        self.registerMonitorDataType(imgWindowDT)


    @staticmethod
    def imgToJson(displayImg: Image):
        try:
            retval, buffer = cv2.imencode(".png", displayImg.mat)
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return None

        return base64.b64encode(buffer).decode("utf-8")

    @staticmethod
    def prepareImgForDisplay(img: Image, settings) -> Image:
        mat = img.mat

        try:
            # Resize creates a copy of the image, important since orig data should not be changed!
            w = 200
            h = 200

            if settings is not None:
                if "w" in settings:
                    w = max(1, math.floor(settings["w"]))
                if "h" in settings:
                    h = max(1, math.floor(settings["h"]))
            mat = cv2.resize(mat, (w, h))  # Creates a copy since dst is not set

            if "mult" in settings and settings["mult"] is not None:
                mul = settings["mult"]
                mat = mat * mul

            # Convert to uint8 to display
            if mat.dtype != 'uint8':
                cv2.normalize(mat, mat, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

            img.mat = mat
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

        return img

    # -------------------------------- IMAGE DT --------------------------------

    @staticmethod
    def displayImageRaw(img, settings):
        return ImageProcModule.prepareImgForDisplay(Image(img.mat), settings)

    @staticmethod
    def displayImageGrayscale(img, settings):
        img = ImageProcModule.prepareImgForDisplay(Image(img.mat), settings)

        shape = img.mat.shape

        if len(shape) == 3:
            img.mat = cv2.cvtColor(img.mat, cv2.COLOR_BGR2GRAY)
            return img
        elif len(shape) == 4:
            img.mat = cv2.cvtColor(img.mat, cv2.COLOR_BGRA2GRAY)
            return img

        return img

    @staticmethod
    def displayImageHistogram(img, settings):
        mat = img.mat

        histoData = []
        for i in range(0, mat.shape[2] if len(mat.shape) > 2 else 1):
            # Calc Histo
            hist = cv2.calcHist([mat], [i], None, [256], [0, 256]).flatten().tolist()
            histoData.append(hist)

        return ScatterplotD(histoData)

    # -------------------------------- ARRAY IMAGE DT --------------------------------

    @staticmethod
    def displayImgArrayDelta(array, settings):
        le = len(array)

        if le == 0:
            return None
        elif le == 1:
            return ImageProcModule.prepareImgForDisplay(Image(array[0].mat), settings)

        # Calc delta between first and last element
        delta = cv2.subtract(array[le - 1].mat, array[0].mat)
        return ImageProcModule.prepareImgForDisplay(Image(delta), settings)

    @staticmethod
    def displayImgArraySum(array, settings):
        le = len(array)

        if le == 0:
            return None
        elif le == 1:
            return ImageProcModule.prepareImgForDisplay(Image(array[0].mat), settings)

        res = array[0].mat

        for i in range(1, le):
            res = cv2.add(res, array[i].mat)

        return ImageProcModule.prepareImgForDisplay(Image(res), settings)
