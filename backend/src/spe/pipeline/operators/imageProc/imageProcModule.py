import logging
import math
import traceback

import cv2

from spe.pipeline.operators.base.dataTypes.scatterplotD import ScatterplotD
from spe.common.dataType import DataType
from spe.pipeline.operators.imageProc.advisorStrategies.grayInputStrategy import GrayInputStrategy
from spe.pipeline.operators.imageProc.dataTypes.image import Image, ImageType
from spe.pipeline.operators.module import Module, MonitorDataType
from streamVizzard import StreamVizzard


class ImageProcModule(Module):
    def __init__(self):
        super(ImageProcModule, self).__init__("ImageProc")

    def initialize(self):
        self.registerOp("spe.pipeline.operators.imageProc.sources.videoFile", "VideoFile", "Sources/VideoFile")

        if not StreamVizzard.isDockerExecution():
            self.registerOp("spe.pipeline.operators.imageProc.sources.webcam", "WebCam", "Sources/WebCam")

        self.registerOp("spe.pipeline.operators.imageProc.operators.process.threshold", "Threshold", "Operators/Process/Threshold")
        self.registerOp("spe.pipeline.operators.imageProc.operators.transform.convert", "Convert", "Operators/Transform/Convert")
        self.registerOp("spe.pipeline.operators.imageProc.operators.process.eqHistogram", "EqHistogram", "Operators/Process/EqHistogram")
        self.registerOp("spe.pipeline.operators.imageProc.operators.transform.imgSplit", "ImgSplit", "Operators/Transform/ImgSplit")
        self.registerOp("spe.pipeline.operators.imageProc.operators.transform.extractROI", "ExtractROI", "Operators/Transform/ExtractROI")
        self.registerOp("spe.pipeline.operators.imageProc.operators.process.gaussianBlur", "GaussianBlur", "Operators/Process/GaussianBlur")
        self.registerOp("spe.pipeline.operators.imageProc.operators.math.imgMultiply", "ImgMultiply", "Operators/Math/ImgMultiply")
        self.registerOp("spe.pipeline.operators.imageProc.operators.math.imgAdd", "ImgAdd", "Operators/Math/ImgAdd")
        self.registerOp("spe.pipeline.operators.imageProc.operators.math.imgBlend", "ImgBlend", "Operators/Math/ImgBlend")
        self.registerOp("spe.pipeline.operators.imageProc.operators.transform.imgMerge", "ImgMerge", "Operators/Transform/ImgMerge")
        self.registerOp("spe.pipeline.operators.imageProc.operators.transform.imgResize", "ImgResize", "Operators/Transform/ImgResize")
        self.registerOp("spe.pipeline.operators.imageProc.operators.process.canny", "Canny", "Operators/Process/Canny")
        self.registerOp("spe.pipeline.operators.imageProc.operators.process.findContours", "FindContours", "Operators/Process/FindContours")

        self.registerOp("spe.pipeline.operators.imageProc.operators.transform.imgLoad", "ImgLoad", "Operators/Transform/ImgLoad")

        DataType.register(ImageType.ImageDTD())

        imgDT = MonitorDataType("IMAGE", lambda x: isinstance(x, Image))
        imgDT.registerDisplayMode(0, self.displayImageRaw)  # Raw
        imgDT.registerDisplayMode(1, self.displayImageGrayscale)  # Grayscale
        imgDT.registerDisplayMode(2, self.displayImageHistogram)  # Histogram
        self.registerMonitorDataType(imgDT)

        imgArrayDT = MonitorDataType("ARRAY_IMG", lambda x: MonitorDataType.isArrayOf(x, Image))
        imgArrayDT.registerDisplayMode(0, lambda x, y: len(x))  # Count
        imgArrayDT.registerDisplayMode(1, self.displayImgArrayDelta)  # Delta
        imgArrayDT.registerDisplayMode(2, self.displayImgArraySum)  # Sum
        self.registerMonitorDataType(imgArrayDT)

        # Transform Image Window to Image Array
        imgWindowDT = MonitorDataType("WINDOW_IMG", lambda x: MonitorDataType.isWindowOf(x, Image))
        imgWindowDT.registerTransformFunc(lambda x: x.toDataArray())
        self.registerMonitorDataType(imgWindowDT)

        # ------ Advisor Strategies ------
        self.registerAdvisorStrategy(["spe.pipeline.operators.imageProc.operators.process.eqHistogram.EqHistogram",
                                      "spe.pipeline.operators.imageProc.operators.process.findContours.FindContours",
                                      "spe.pipeline.operators.imageProc.operators.process.threshold.Threshold"], GrayInputStrategy)

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
