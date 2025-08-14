from typing import Dict

from py2neo.cypher import Cursor

from spe.runtime.debugger.provenance.provQueryParser import ProvQueryParser
from spe.runtime.debugger.provenance.provenanceInspector import ProvenanceInspector
from spe.runtime.debugger.provenance.queryTemplates.queryTemplate import QueryTemplate, QueryTarget, QueryOpTargetType


class UpdateImpactQT(QueryTemplate):
    def __init__(self, inputData):
        super().__init__(QueryTarget.UPDATE_IMPACT, inputData)

    def generateQuery(self) -> str:
        chains = self.inputData["chains"]

        for chain in chains:
            if chain["chainKey"] == "opTarget":
                opID = chain["opID"]
                opTargetType = QueryOpTargetType.parse(chain["opTargetType"])  # Metric
                opTargetValue = chain["opTargetValue"]  # Throughput, ...
            elif chain["chainKey"] == "condition":
                limit = chain["limit"]
                ordering = chain["returnOrder"]
                comparator = chain["comparator"]  # > < = ...
                compValue = ProvQueryParser.parseInputValue(chain["value"])

        query = ""

        return query

    def extractResult(self, inspector: ProvenanceInspector, result: Cursor) -> Dict:
        pass
