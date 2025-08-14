from __future__ import annotations

from typing import Optional

from spe.runtime.debugger.provenance.queryTemplates.queryTemplate import QueryTarget, QueryTemplate


class ProvQueryParser:
    @staticmethod
    def createQueryTemplate(inputData) -> Optional[QueryTemplate]:
        target = QueryTarget.parse(inputData["target"])

        if target is None:
            return None

        return QueryTemplate.getTemplateForTarget(target, inputData)

    @staticmethod
    def parseInputValue(inputVal: str) -> str:
        try:
            float(inputVal)

            return inputVal
        except ValueError:
            return "'" + inputVal + "'"
