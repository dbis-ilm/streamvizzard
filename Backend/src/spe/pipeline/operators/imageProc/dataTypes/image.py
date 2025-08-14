from __future__ import annotations
import base64
import logging
import traceback
from typing import Any, Dict, Optional, Type

import cv2
import numpy as np

from spe.common.dataType import DataType
from spe.common.serialization.serializationMode import SerializationMode


class Image:
    def __init__(self, mat):
        self.mat = mat

    def getWidth(self):
        return self.mat.shape[1]

    def getHeight(self):
        return self.mat.shape[0]

    def isGrey(self):
        return not (len(self.mat.shape) != 2 and self.mat.shape[2] != 1)

    def clone(self):
        return Image(self.mat.copy())

    def toJSON(self) -> Optional[str]:
        bts = self.toBytes()

        if bts is not None:
            return bts.decode("utf-8")

        return None

    def toBytes(self) -> Optional[bytes]:
        try:
            retval, buffer = cv2.imencode(".png", self.mat)
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return None

        return base64.b64encode(buffer)

    @staticmethod
    def fromBytes(data: bytes) -> Optional[Image]:
        try:
            np_arr = np.frombuffer(data, np.uint8)
            mat = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

            return Image(mat)
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return None

    @staticmethod
    def fromJSON(data: str) -> Optional[Image]:
        return Image.fromBytes(base64.b64decode(data))


class ImageType(DataType):
    name = "Image"

    class ImageDTD(DataType.Definition):
        def __init__(self):
            super().__init__(ImageType.name)

            self.registerSerializer(SerializationMode.JSON, lambda img: img.toJSON())
            self.registerDeserializer(SerializationMode.JSON, Image.fromJSON)

            self.registerSerializer(SerializationMode.BYTES, lambda img: img.toBytes())
            self.registerDeserializer(SerializationMode.BYTES, Image.fromBytes)

        def getValueType(self) -> Optional[Type]:
            return Image

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            return ImageType(self)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            return ImageType(self)

    def __init__(self, definition: ImageDTD):
        super().__init__(definition, uniform=True)
