from abc import ABC

from spe.pipeline.operators.operator import Operator
from spe.runtime.compiler.definitions.compileOpMetaData import CompileOpMetaData


class WindowOperator(Operator, ABC):
    @property
    def allowedChildren(self):
        from spe.pipeline.operators.base.operators.windows.windowProcessor import WindowProcessor
        return [WindowProcessor]

    def getCompileMetaData(self) -> CompileOpMetaData:
        return CompileOpMetaData(inheritTarget=True)

    # -------------------------- Compilation -------------------------

    @staticmethod
    def _getPyFlinkCompileAssignment(windowFunc: str, parallelism: int) -> str:
        # window_all for non-keyed streams with para=1, else we need a keyed window

        if parallelism == 1:
            return "$inDS.window_all(" + windowFunc + ")"
        else:
            # Care: Window groups by key and trigger [count/time]! [count=5 & 5 distinct keys -> 5 tuples PER key]
            return f"$inDS.$keyBy.window(" + windowFunc + ")"
