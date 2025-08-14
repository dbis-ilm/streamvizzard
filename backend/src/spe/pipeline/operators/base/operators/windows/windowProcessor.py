from abc import ABC

from spe.pipeline.operators.operator import Operator
from spe.runtime.compiler.definitions.compileOpMetaData import CompileOpMetaData


class WindowProcessor(Operator, ABC):
    @property
    def allowedParents(self):
        from spe.pipeline.operators.base.operators.windows.windowOperator import WindowOperator
        return [WindowOperator]

    def getCompileMetaData(self) -> CompileOpMetaData:
        # Formally, the processor could have a different level of parallelism compare to the window operator.
        # For simplicity during placement and compilation (cant serialize window) we enforce the same target here.
        return CompileOpMetaData(inheritTarget=True)
