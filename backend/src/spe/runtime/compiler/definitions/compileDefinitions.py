from __future__ import annotations
from enum import Enum
from typing import Optional, List


class CompileFramework(Enum):
    STREAMVIZZARD = "StreamVizzard"
    PYFLINK = "PyFlink"

    @staticmethod
    def all():
        return [e for e in CompileFramework]

    @staticmethod
    def parse(value: str) -> Optional[CompileFramework]:
        for e in CompileFramework:
            if e.value == value:
                return e

        return None


class CompileFrameworkConnector(Enum):
    SOCKET_TEXT_SERVER = "Socket Text Server"
    SOCKET_TEXT_CLIENT = "Socket Text Client"
    APACHE_KAFKA = "Apache Kafka"

    @staticmethod
    def parse(value: str) -> Optional[CompileFrameworkConnector]:
        for e in CompileFrameworkConnector:
            if e.value == value:
                return e

        return None

    def getCompatible(self):
        if self == CompileFrameworkConnector.SOCKET_TEXT_CLIENT:
            return [CompileFrameworkConnector.SOCKET_TEXT_SERVER]
        elif self == CompileFrameworkConnector.SOCKET_TEXT_SERVER:
            return [CompileFrameworkConnector.SOCKET_TEXT_CLIENT]
        elif self == CompileFrameworkConnector.APACHE_KAFKA:
            return [CompileFrameworkConnector.APACHE_KAFKA]
        return None


class CompileLanguage(Enum):
    PYTHON = "Python"

    @staticmethod
    def parse(value: str) -> Optional[CompileLanguage]:
        for e in CompileLanguage:
            if e.value == value:
                return e

        return None


class CompileParallelism(Enum):
    SINGLE_NODE = "Single Node"
    DISTRIBUTED = "Distributed"

    @staticmethod
    def all():
        return [e for e in CompileParallelism]

    @staticmethod
    def parse(value: str) -> Optional[CompileParallelism]:
        for e in CompileParallelism:
            if e.value == value:
                return e

        return None

    @staticmethod
    def orderList(ems: List[CompileParallelism]):
        # Return a list ordered by appearance of values in this enum

        res = []

        for em in CompileParallelism:
            if em in ems:
                res.append(em)

        return res


class CompileComputeMode(Enum):
    CPU = "CPU"
    GPU = "GPU"

    @staticmethod
    def parse(value: str) -> Optional[CompileComputeMode]:
        for e in CompileComputeMode:
            if e.value == value:
                return e

        return None

    @staticmethod
    def orderList(tms: List[CompileComputeMode]):
        # Return a list ordered by appearance of values in this enum

        res = []

        for tm in CompileComputeMode:
            if tm in tms:
                res.append(tm)

        return res
