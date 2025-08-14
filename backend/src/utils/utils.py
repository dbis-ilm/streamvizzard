import sys
import warnings
from typing import Dict, Any


def remap(val, sourceFrom, sourceTo, targetFrom, targetTo):
    return (val - sourceFrom) / (sourceTo - sourceFrom) * (targetTo - targetFrom) + targetFrom


def clamp(val, minV, maxV):
    return max(minV, min(val, maxV))


def tryParseInt(value: str, default) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def tryParseFloat(value: str, default) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parseBool(value: str) -> bool:
    return value.lower() in ('true', '1', 'yes', 'on')


def valueOr(value, defaultVal):
    if value is not None:
        return value
    return defaultVal


def escapeStr(data: str, encode: bool) -> str:
    if encode:  # Escapes all control sequences \n => \\n
        return data.encode('unicode_escape').decode("utf-8")
    else:  # Removes escapes from control sequences \\n => \n
        return data.encode('utf-8').decode('unicode_escape')


def escapeStrInDict(data: Dict[Any, str], encode: bool) -> Dict:
    data = data.copy()  # Make sure not to override original data

    for k in data.keys():
        data[k] = escapeStr(data[k], encode)

    return data


def printWarning(msg: str):
    warnings.warn(msg, stacklevel=2)


def isWindowsOS():
    return sys.platform.startswith('win')


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
