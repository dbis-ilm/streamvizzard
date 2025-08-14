from __future__ import annotations

import abc
from enum import Enum
from typing import Callable, TYPE_CHECKING, Optional

from spe.runtime.compiler.codegeneration.codeTemplate import CodeTemplate
from spe.runtime.compiler.codegeneration.nativeCodeExtractor import NativeCodeExtractor

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.compiler.opCompileConfig import OpCompileConfig


class CompileOpFunction(abc.ABC):
    class Type(Enum):
        SOURCE = "source"
        MAP = "map"
        FILTER = "filter"
        WINDOW = "window"
        SINK = "sink"
        OTHER = "other"

    def __init__(self, functionType: Type):
        self.functionType = functionType


# This COF will take the python execution code from the StreamVizzard System
class InferExecutionCodeCOF(CompileOpFunction):
    def __init__(self, functionType: CompileOpFunction.Type,
                 inputRenamer: Optional[tuple[str, str]] = None):
        super().__init__(functionType)

        self.inputRenamer = inputRenamer

    def infer(self, op: Operator, cfg: Optional[OpCompileConfig]) -> Optional[NativeCodeExtractor]:
        extr = NativeCodeExtractor.fromClassMethod(op, targetClass=op.__class__, targetFuncName=op._execute.__name__)

        if extr is None:
            return None

        self._prepareExtract(extr)

        # Only return body of execute function, not the function itself
        extr.discardFuncSignature(op._execute.__name__)

        return extr

    def performInputRenaming(self, extr: NativeCodeExtractor):
        if self.inputRenamer is not None:
            extr.renameVar(self.inputRenamer[0], self.inputRenamer[1])

    @staticmethod
    def _prepareExtract(extr: NativeCodeExtractor) -> NativeCodeExtractor:
        extr.convertParams()
        extr.replaceSVInternals()

        return extr

    @staticmethod
    def canAutoInfer(op: Operator) -> bool:
        """ Performs a test inference of the code to check if it is supported. """

        NativeCodeExtractor.toggleWarnings(False)

        extr = InferExecutionCodeCOF(InferExecutionCodeCOF.Type.MAP).infer(op, None)

        if extr is None:
            return False

        res = extr.extract(False)

        NativeCodeExtractor.toggleWarnings(True)

        return res is not None


class InferCustomCodeCOF(InferExecutionCodeCOF):
    def __init__(self, functionType: CompileOpFunction.Type,
                 codeGetter: Callable[[OpCompileConfig], str],
                 inputRenamer: Optional[tuple[str, str]] = None):
        super().__init__(functionType, inputRenamer)

        self.codeGetter = codeGetter

    def infer(self, op: Operator, cfg: OpCompileConfig) -> Optional[NativeCodeExtractor]:
        code = self.codeGetter(cfg)

        extr = NativeCodeExtractor.fromRawCode(op, rawCode=code)

        if extr is None:
            return None

        self._prepareExtract(extr)

        return extr


class CodeTemplateCOF(CompileOpFunction):
    def __init__(self, functionType: CompileOpFunction.Type, templateGetter: Callable[[OpCompileConfig], CodeTemplate]):
        super().__init__(functionType)

        self.templateGetter = templateGetter
