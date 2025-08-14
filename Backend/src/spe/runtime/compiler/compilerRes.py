from typing import Optional


class CompilerRes:
    def __init__(self, errorMsg: Optional[str] = None, statusMsg: Optional[str] = None):
        self.errorMsg = errorMsg
        self.success = errorMsg is None
        self.statusMsg = statusMsg

    def hasError(self) -> bool:
        return self.errorMsg is not None

    def toJSON(self):
        return self.__dict__

    @staticmethod
    def ok(statusMsg: Optional[str] = None):
        return CompilerRes(statusMsg=statusMsg)

    @staticmethod
    def error(errorMsg: str):
        return CompilerRes(errorMsg=errorMsg)
