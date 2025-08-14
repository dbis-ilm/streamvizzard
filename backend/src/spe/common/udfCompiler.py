import re

from spe.common.dataType import DataType


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

    from spe.common.tuple import Tuple
    loc = {"Tuple": Tuple}

    # Register custom data types to use
    for ct in DataType.getCustomTypes():
        loc[ct.getValueTypeName()] = ct.getValueType()

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


def instantiateUserDefinedFunction(operator, c):
    code = ""

    # TODO: We could optimize execution by extracting imports with AST
    lines = c.split("\n")

    code += "def func(input):\n"

    # Insert function code

    for line in lines:
        code += "\n    " + line

    # If exec gets two separate objects as globals and locals, the code will be executed
    # as if it were embedded in a class definition -> Use same, empty loc

    loc = {}

    # Register custom data types to use
    for ct in DataType.getCustomTypes():
        loc[ct.getValueTypeName()] = ct.getValueType()

    try:
        exec(compile(code, "", "exec"), loc, loc)

        return loc[f"func"]
    except Exception:
        operator.onExecutionError()

        return None
