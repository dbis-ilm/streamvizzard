import re
import sys
import warnings


def remap(val, from1, to1, from2, to2):
    return (val - from1) / (to1 - from1) * (to2 - from2) + from2


def clamp(val, minV, maxV):
    return max(minV, min(val, maxV))


def createUDFFunction(c: str, includePersistent: bool) -> str:
    code = ""

    lines = c.split("\n")

    # Global store + function register

    if includePersistent:
        code += "store = persistent\n"

    code += "def func(input, tuple):\n"

    if includePersistent:
        code += "\n    global store"

    # Insert function code

    for line in lines:
        code += "\n    " + line

    # Function call and result

    code += "\nres = func(data, tuple)"

    if includePersistent:
        code += "\npersistent = store"

    return code


def instantiateUserDefinedClass(operator, code, oldInstance):
    # Destroy old instance

    if oldInstance is not None:
        oldInstance.onDestroy()

    # Extract className from data (first occurrence)

    className = None

    m = re.search('(?<=class)(.*)', code)
    if m:
        className = m.groups()[0].replace(":", "").strip()

    if className is None:
        return None

    # Instantiate object of class

    from spe.runtime.structures.tuple import Tuple
    loc = {"Tuple": Tuple}

    # If exec gets two separate objects as globals and locals, the code will be executed
    # as if it were embedded in a class definition -> Use same, empty loc
    try:
        exec(compile(code, className, "exec"), loc, loc)
    except Exception:
        operator.onExecutionError()

        return None

    newInstance = loc[className]()
    newInstance.baseOp = operator

    # Initialize new instance

    if newInstance is not None:
        newInstance.onStart()

    return newInstance


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
