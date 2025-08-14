from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import Dict, Optional, List

from py2neo import Node
from py2neo.cypher import Cursor

from spe.runtime.debugger.provenance.provQueryParser import ProvQueryParser
from spe.runtime.debugger.provenance.provenanceInspector import ProvenanceInspector
from spe.runtime.debugger.provenance.queryTemplates.queryTemplate import QueryTemplate, QueryTarget, QueryOpTargetType


# We should look on the current pipelineVersionRevision as a join between metrics and params.
# If updates occurred we refresh metrics on next execution (prev metrics are outdated if sth. changed)
# Only issue: Unchanged ops might not have updated metrics registered, so we need to access those somehow???
# Not possible in the query since we don't know relations of ops there,... -> invalidate ALL metrics to be sure?
# Downside: More graph nodes / complexity + all ops need to process tuples before queries can return results
# Second Point doesn't matter and first prob not big difference

class ReturnParam(ABC):
    def __init__(self, idx: int, opIdx: int):
        self.idx = idx
        self.opIdx = opIdx

    @abstractmethod
    def generateQuery(self, targetVal: str, comparator: str, compValue: str, prevParam: Optional[ReturnParam]) -> str:
        ...

    @abstractmethod
    def getReturnStr(self) -> str:
        ...

    @abstractmethod
    def getOrderStr(self) -> str:
        ...

    def extractData(self, row) -> Dict:
        param: Node = row["m" + str(self.idx)]

        return {"name": param.get("name"), "value": param.get("value")}

    @abstractmethod
    def getStepID(self, row) -> int:
        ...

    def getBranchID(self, row) -> Optional[int]:
        pv = row["pv" + str(self.idx)]

        try:
            return int(pv.get("id"))
        except ValueError:
            return None


class MetricReturn(ReturnParam):
    def __init__(self, idx: int, opIdx: int):
        super().__init__(idx, opIdx)

    def generateQuery(self, targetVal: str, comparator: str, compValue: str, prevParam: Optional[ReturnParam]) -> str:
        idStr = str(self.idx)

        return (
                # Extract metric information from the OperatorExecution node

                "MATCH (op" + idStr + ":Entity {"
                "    `prov:type`: \"Operator\", `id`: " + str(self.opIdx) +
                "})-[:specializationOf]-(opr" + idStr + ":Entity {"
                "    `prov:type`: \"OperatorRevision\""
                "})-[:used]-(opex" + idStr + ":Activity {"
                "    `prov:type`: \"OperatorExecution\""
                "})-[:wasGeneratedBy]-(m" + idStr + ":Entity {"
                "    `prov:type`: \"Metric\", `name`: \"" + targetVal + "\""
                "}) WHERE m" + idStr + ".value " + comparator + " " + compValue +

                # Connect OperatorRevision to PipelineVersion to access branchID and join with prev RP

                " MATCH (pv" + idStr + ":Entity {"
                "    `prov:type`: \"PipelineVersion\""
                "})-[:specializationOf]-(pvr" + idStr + ":Entity {"
                "    `prov:type`: \"PipelineVersionRevision\""
                "})-[:hadMember]-(opr" + idStr + ")" +
                ("" if prevParam is None else " WHERE pvr" + idStr + ".uuid = pvr" + str(prevParam.idx) + ".uuid")
            )

    def getReturnStr(self) -> str:
        return "m" + str(self.idx) + ", opex" + str(self.idx) + ", pv" + str(self.idx)

    def getOrderStr(self) -> str:
        return "m" + str(self.idx) + ".value DESC"

    def getStepID(self, row) -> Optional[int]:
        ex: Node = row["opex" + str(self.idx)]

        try:
            return int(ex.get("step_id"))
        except ValueError:
            return None


class ParamReturn(ReturnParam):
    def __init__(self, idx: int, opIdx: int):
        super().__init__(idx, opIdx)

    def generateQuery(self, targetVal: str, comparator: str, compValue: str, prevParam: Optional[ReturnParam]) -> str:
        idStr = str(self.idx)

        return (
                # Extract param information from OperatorRevision node
                                                    
                "MATCH (op" + idStr + ":Entity {"
                "    `prov:type`: \"Operator\", `id`: " + str(self.opIdx) +
                "})-[:specializationOf]-(opr" + idStr + ":Entity {"
                "    `prov:type`: \"OperatorRevision\""
                "})-[:hadMember]-(m" + idStr + ":Entity {"
                "   `prov:type`: \"Parameter\", `name`: \"" + targetVal + "\""
                "}) WHERE m" + idStr + ".value " + comparator + " " + compValue +

                # Connect OperatorRevision to PipelineVersion to access branchID and join with prev RP pvr

                " MATCH (pv" + idStr + ":Entity {"
                "    `prov:type`: \"PipelineVersion\""
                "})-[:specializationOf]-(pvr" + idStr + ":Entity {"
                "    `prov:type`: \"PipelineVersionRevision\""
                "})-[:hadMember]-(opr" + idStr + ")" +
                ("" if prevParam is None else " WHERE pvr" + idStr + ".uuid = pvr" + str(prevParam.idx) + ".uuid") +

                # Either match with the corresponding PipelineChange [Updates] or PipelineVersionCreation [Initial]

                " OPTIONAL MATCH (opr" + idStr +
                ")-[:wasGeneratedBy]-(pc" + idStr + ":Activity {"
                "   `prov:type`: \"PipelineChange\""
                "}) "
    
                " OPTIONAL MATCH (pvr" + idStr +
                ")-[:wasGeneratedBy]-(pvc" + idStr + ":Activity {"
                "   `prov:type`: \"PipelineVersionCreation\""
                "}) "
        )

    def getReturnStr(self) -> str:
        return "m" + str(self.idx) + ", pc" + str(self.idx) + ", pvr" + str(self.idx) + ", pv" + str(self.idx)

    def getOrderStr(self) -> str:
        return "m" + str(self.idx) + ".value DESC"

    def getStepID(self, row) -> Optional[int]:
        pc: Node = row["pc" + str(self.idx)]
        pvr: Node = row["pvr" + str(self.idx)]

        if pc is not None:
            try:
                return int(pc.get("step_id"))
            except ValueError:
                return None

        if pvr is not None:
            return 0  # Start of new branch

        return None


class FindOptimumQT(QueryTemplate):
    def __init__(self, inputData):
        super().__init__(QueryTarget.FIND_OPTIMUM, inputData)

        self.queryParams: List[ReturnParam] = list()

    def generateQuery(self) -> str:
        chains = self.inputData["chains"]

        conditions = []
        limit = 1

        for chain in chains:
            if chain["chainKey"] == "condition":
                conditions.append(chain)
            elif chain["chainKey"] == "limit":
                limit = chain["limit"]

        query = ""

        for condition in conditions:
            currentCondID = len(self.queryParams) + 1

            opID = condition["opID"]
            opTargetType = QueryOpTargetType.parse(condition["opTargetType"])  # Metric, Param, ...
            opTargetValue = condition["opTargetValue"]  # Throughput, ..., or params of op
            comparator = condition["comparator"]  # > < = ...
            compValue = ProvQueryParser.parseInputValue(condition["value"])
            logicChain = condition["logicChain"]  # Currently unused, always linked as AND

            paramReturn = MetricReturn(currentCondID, opID) if opTargetType == QueryOpTargetType.METRIC else ParamReturn(currentCondID, opID)
            prevParamReturn = self.queryParams[-1] if len(self.queryParams) > 0 else None

            query += " " + paramReturn.generateQuery(opTargetValue, comparator, compValue, prevParamReturn)

            self.queryParams.append(paramReturn)

        query += " RETURN DISTINCT " + ",".join([pr.getReturnStr() for pr in self.queryParams])

        query += " ORDER BY " + ",".join([pr.getOrderStr() for pr in self.queryParams])

        query += " LIMIT " + str(limit)

        print(query)

        return query

    def extractResult(self, inspector: ProvenanceInspector, result: Cursor) -> Dict:
        print(repr(result.preview(sys.maxsize)))

        optimums = []

        rows = result.data()

        for row in rows:
            branchID = -1
            stepID = -1

            params = []

            for pv in self.queryParams:
                branchID = pv.getBranchID(row)  # All param will have same branchID due to join
                params.append(pv.extractData(row))

                sID = pv.getStepID(row)

                if sID is not None and sID > stepID:
                    stepID = sID

            step = self._receiveStep(branchID, stepID, inspector)

            if step is None:
                continue

            optimums.append({"branchID": branchID, "stepID": stepID, "stepTime": step.time, "params": params})

        return {"res": optimums}
