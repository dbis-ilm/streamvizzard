from __future__ import annotations
import random
from typing import Tuple, TYPE_CHECKING

import cv2
import numpy as np

from analysis.costModel.configurations.costModelOpSetups import CostModelOpSetups, \
    OpInputDataFeature, OpParamFeature, CostModelOpCfg
from analysis.costModel.executionRecording import RecordingParam
from analysis.costModel.costModel import CostModelTarget, CostModelEnv
from spe.pipeline.operators.imageProc.dataTypes.image import Image


if TYPE_CHECKING:
    from analysis.costModel.costModelAnalysis import CostModelAnalysis


class ImageProcessingConf(CostModelOpSetups):
    def __init__(self, runCanny: bool = True, runGaussian: bool = True, runHisto: bool = True,
                 runConvert: bool = True, runThresh: bool = True, runContours: bool = True, runCrop: bool = True):
        super(ImageProcessingConf, self).__init__()

        self._runCanny = runCanny
        self._runGaussian = runGaussian
        self._runHisto = runHisto
        self._runConvert = runConvert
        self._runThresh = runThresh
        self._runContours = runContours
        self._runCrop = runCrop

        self._its = 1_000
        self._repetition = 10

    def registerRuns(self, cma: CostModelAnalysis):
        if self._runCanny:
            from spe.pipeline.operators.imageProc.operators.process.canny import Canny

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(Canny),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateImage(),
                                   lambda runID: {"threshold1": random.randrange(0, 256),
                                                  "threshold2": random.randrange(0, 256),
                                                  "aperture": random.randrange(3, 7, 2)},
                                   lambda tup, op: [RecordingParam("width", tup[0].mat.shape[1]),
                                                    RecordingParam("height", tup[0].mat.shape[0]),
                                                    RecordingParam("total", tup[0].mat.shape[1] * tup[0].mat.shape[0]),
                                                    RecordingParam("threshold1", op.threshold1),
                                                    RecordingParam("threshold2", op.threshold2),
                                                    RecordingParam("aperture", op.aperture)],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("total"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1]),
                                               OpParamFeature("aperture",
                                                              lambda res: res.getValue("aperture"),
                                                              lambda op: op.aperture)],
                                   ),
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.OUTPUT_SIZE,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("total"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1])]
                                   )
                               ]))

        if self._runGaussian:
            from spe.pipeline.operators.imageProc.operators.process.gaussianBlur import GaussianBlur

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(GaussianBlur),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateImage(),
                                   lambda runID: {"kernelX": random.randrange(1, 51, 2),
                                                  "kernelY": random.randrange(1, 51, 2),
                                                  "sigmaX": random.randrange(1, 9),
                                                  "sigmaY": random.randrange(1, 9)},
                                   lambda tup, op: [
                                       RecordingParam("width", tup[0].mat.shape[1]),
                                       RecordingParam("height", tup[0].mat.shape[0]),
                                       RecordingParam("total", tup[0].mat.shape[1] * tup[0].mat.shape[0]),
                                       RecordingParam("kernelX", op.kernelX),
                                       RecordingParam("kernelY", op.kernelY),
                                       RecordingParam("sigmaX", op.sigmaX),
                                       RecordingParam("sigmaY", op.sigmaY)],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("total"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1]),
                                               OpParamFeature("kernelX",
                                                              lambda res: res.getValue("kernelX"),
                                                              lambda op: op.kernelX),
                                               OpParamFeature("kernelY",
                                                              lambda res: res.getValue("kernelY"),
                                                              lambda op: op.kernelY)],
                                   ),
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.OUTPUT_SIZE,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("total"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1])],
                                   )
                               ]))

        if self._runHisto:
            from spe.pipeline.operators.imageProc.operators.process.eqHistogram import EqHistogram

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(EqHistogram),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateImage(True),
                                   lambda runID: {},
                                   lambda tup, op: [
                                       RecordingParam("width", tup[0].mat.shape[1]),
                                       RecordingParam("height", tup[0].mat.shape[0]),
                                       RecordingParam("total", tup[0].mat.shape[1] * tup[0].mat.shape[0])],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("total"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1])],
                                   )
                               ]))

        if self._runConvert:
            from spe.pipeline.operators.imageProc.operators.transform.convert import Convert

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(Convert),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateImage(),
                                   lambda runID: {"mode": random.choice(["grayscale", "float32"])},
                                   lambda tup, op: [
                                       RecordingParam("width", tup[0].mat.shape[1]),
                                       RecordingParam("height", tup[0].mat.shape[0]),
                                       RecordingParam("total", tup[0].mat.shape[1] * tup[0].mat.shape[0]),
                                       RecordingParam("mode", op.mode)],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("total"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1]),
                                               OpParamFeature("mode",
                                                              lambda res: res.getValue("mode"),
                                                              lambda op: op.mode)],
                                   ),
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.OUTPUT_SIZE,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("total"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1]),
                                               OpParamFeature("mode",
                                                              lambda res: res.getValue("mode"),
                                                              lambda op: op.mode)],
                                   )
                               ]))

        if self._runThresh:
            from spe.pipeline.operators.imageProc.operators.process.threshold import Threshold

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(Threshold),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateImage(True),
                                   lambda runID: {"threshold": random.randrange(0, 255),
                                                  "maxVal": random.randrange(0, 255),
                                                  "mode": random.choice(["binary", "binaryInv", "trunc", "zero", "zeroInv"])},
                                   lambda tup, op: [
                                       RecordingParam("width", tup[0].mat.shape[1]),
                                       RecordingParam("height", tup[0].mat.shape[0]),
                                       RecordingParam("total", tup[0].mat.shape[1] * tup[0].mat.shape[0]),
                                       RecordingParam("threshold", op.threshold),
                                       RecordingParam("maxValue", op.maxValue),
                                       RecordingParam("mode", op.mode)],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("total"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1])],
                                   )
                               ]))

        if self._runContours:
            from spe.pipeline.operators.imageProc.operators.process.findContours import FindContours

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(FindContours),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateImage(True),
                                   lambda runID: {"mode": random.randint(0, 3),
                                                  "method": random.randint(0, 3),
                                                  "drawThickness": 1},
                                   lambda tup, op: [
                                       RecordingParam("total", tup[0].mat.shape[1] * tup[0].mat.shape[0]),
                                       RecordingParam("width", tup[0].mat.shape[1]),
                                       RecordingParam("height", tup[0].mat.shape[0]),
                                       RecordingParam("method", op.method),
                                       RecordingParam("mode", op.mode)],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("total"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1]),
                                               OpParamFeature("method",
                                                              lambda res: res.getValue("method"),
                                                              lambda op: op.method)]
                                   )
                               ]))

        if self._runCrop:
            from spe.pipeline.operators.imageProc.operators.transform.extractROI import ExtractROI

            cma.registerOperator(
                CostModelOpCfg(self._createOperator(ExtractROI),
                               CostModelOpCfg.OpExecutionCfg(
                                   lambda runID: self._generateImage(True),
                                   lambda runID: {"x": random.randint(1000, 1015),
                                                  "y": random.randint(400, 450),
                                                  "w": random.randint(10, 15),
                                                  "h": random.randint(55, 60)},
                                   lambda tup, op: [
                                       RecordingParam("width", tup[0].mat.shape[1]),
                                       RecordingParam("height", tup[0].mat.shape[0]),
                                       RecordingParam("w", op.w),
                                       RecordingParam("h", op.h)],
                                   iterations=self._its, warmUp=2, repetitions=self._repetition,
                               ),
                               targets=[
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.EXECUTION_TIME,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("width") * res.getValue("height"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1])],
                                   ),
                                   CostModelOpCfg.TargetConfig(
                                       env=CostModelEnv.SV_CPU,
                                       target=CostModelTarget.OUTPUT_SIZE,
                                       inputs=[OpInputDataFeature("total", 0,
                                                                  lambda res: res.getValue("width") * res.getValue("height"),
                                                                  lambda tup: tup[0].mat.shape[0] * tup[0].mat.shape[1])],
                                   )
                               ]))

    @staticmethod
    def _generateImage(grey: bool = False) -> Tuple:
        img = Image(np.random.randint(low=0, high=255, size=(random.randint(480, 3840),
                                                             random.randint(480, 3840), 3),
                                      dtype=np.uint8))

        if grey:
            img.mat = cv2.cvtColor(img.mat, cv2.COLOR_BGR2GRAY)

        return img,
