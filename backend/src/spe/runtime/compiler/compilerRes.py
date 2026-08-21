from typing import Optional

from utils.svResult import SvResult


class CompilerRes(SvResult):
    def __init__(self, errorMsg: Optional[str] = None, result: Optional[str] = None):
        super().__init__(errorMsg)

        self.result = result

    @staticmethod
    def okWithRes(result: str):
        return CompilerRes(result=result)

    @staticmethod
    def error(errorMsg: str):
        return CompilerRes(errorMsg=errorMsg)
