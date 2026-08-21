import logging
import sys
import traceback
import warnings
from typing import Dict, Any, Optional


def remap(val, sourceFrom, sourceTo, targetFrom, targetTo, clamped: bool = False):
    if clamped:
        val = max(min(val, sourceTo), sourceFrom)  # Clamp val first

    return (val - sourceFrom) / (sourceTo - sourceFrom) * (targetTo - targetFrom) + targetFrom


def clamp(val, minV, maxV):
    return max(minV, min(val, maxV))


def tryParseInt(value: str, default: int = 0) -> int:
    if value is None:
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def tryParseFloat(value: str, default: float = 0) -> float:
    if value is None:
        return default

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


def extractTracebackErrorMsg(showErrorLine: bool = False, lineNrOffset: int = 0,
                             logError: bool = False) -> Optional[str]:
    T, V, TB = sys.exc_info()

    if T is None:
        return None

    # Extract error msg from exception

    tb = traceback.extract_tb(TB)
    res = traceback.format_exception_only(T, V)

    error = res[len(res) - 1] + "\n".join(res[:len(res) - 1])

    if showErrorLine:
        error = "[Line " + str(tb[-1].lineno + lineNrOffset) + "] " + error

    if logError:
        logging.log(logging.ERROR, traceback.format_exc())

    return error.strip()


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
