import json
from typing import Optional

import cv2
import numpy as np

from spe.pipeline.operators.imageProc.dataTypes.image import Image
from spe.pipeline.operators.operator import Operator
from spe.common.tuple import Tuple


class ImgMerge(Operator):
    """
    Inputs: 4
    Outputs: 1
    """

    def __init__(self, opID: int):
        super(ImgMerge, self).__init__(opID, 4, 1)

    def setData(self, data: json):
        ...

    def getData(self) -> dict:
        return {}

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        channels = np.asarray(tupleIn.data, dtype=object)

        # Collect mats from Image DT
        for i in range(0, len(channels)):
            if channels[i] is not None:
                channels[i] = channels[i].mat

        # Replace None channels with zeros

        firstNotNoneChannel = None
        hasNoneChannels = False
        for channel in channels:
            if channel is not None:
                firstNotNoneChannel = channel
            else:
                hasNoneChannels = True

        if firstNotNoneChannel is None:
            return None

        if hasNoneChannels:
            for idx in range(0, len(channels)):
                if channels[idx] is None:
                    channels[idx] = np.zeros(firstNotNoneChannel.shape, dtype=np.uint8)

        # Merge

        # If no alpha channel is supplied remove it
        if tupleIn.data[3] is None:
            channels.resize(channels.size - 1)

        res = cv2.merge(channels)

        return self.createTuple((Image(res),))
