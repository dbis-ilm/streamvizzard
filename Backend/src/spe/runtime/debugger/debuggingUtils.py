from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.structures.tuple import Tuple


def retrieveStoredDTRef(operator: Operator, tup: Tuple, refTupleUUID: str) -> Optional[DebugTuple]:
    addedTupID: Tuple = operator.getDebugger().getDT(tup).getAttribute(refTupleUUID)
    inputDt = operator.getDebugger().getDTByTupleID(addedTupID)

    if inputDt is None:
        operator.onExecutionError("DebugTuple not available, memory limits to small?")
        return None

    return inputDt
