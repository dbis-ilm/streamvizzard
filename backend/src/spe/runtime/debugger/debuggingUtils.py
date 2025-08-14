from typing import Optional

from spe.pipeline.operators.operator import Operator
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.common.tuple import Tuple
from utils.messages import Messages


def retrieveStoredDTRef(operator: Operator, tup: Tuple, refTupleUUID: str) -> Optional[DebugTuple]:
    addedTupID: Optional[Tuple] = operator.getDebugger().getDT(tup).getAttribute(refTupleUUID)

    if addedTupID is None:  # No tuple stored
        return None

    inputDt = operator.getDebugger().getDTByTupleID(addedTupID)

    if inputDt is None:
        operator.onExecutionError(Messages.DEBUGGER_DT_NOT_AVAILABLE.value)
        return None

    return inputDt
