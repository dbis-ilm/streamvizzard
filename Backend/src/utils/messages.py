from enum import Enum


class Messages(Enum):
    DEBUGGER_DT_NOT_AVAILABLE = "DebugTuple not available, memory limits to small?"
    DEBUGGER_OP_NOT_SUPPORTED = "Operator does not support debugging!"
