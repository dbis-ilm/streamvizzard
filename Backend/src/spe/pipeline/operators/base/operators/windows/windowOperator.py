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
