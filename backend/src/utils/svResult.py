from typing import Optional


class SvResult:
    def __init__(self, errorMsg: Optional[str] = None):
        self.errorMsg = errorMsg

    def hasError(self) -> bool:
        return self.errorMsg is not None

    @staticmethod
    def ok():
        return SvResult()

    @staticmethod
    def error(errorMsg: str):
        return SvResult(errorMsg)
