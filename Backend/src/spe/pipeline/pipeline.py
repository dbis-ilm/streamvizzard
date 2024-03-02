from __future__ import annotations
import asyncio
from typing import List, Dict, Optional, TYPE_CHECKING

from spe.pipeline.connection import Connection

from spe.runtime.structures.iEventEmitter import IEventEmitter

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.pipeline.operators.source import Source


class Pipeline(IEventEmitter):
    EVENT_PIPELINE_PRE_UPDATED = "PrePipeUpdated"  # [PipelineUpdate]
    EVENT_PIPELINE_UPDATED = "PipeUpdated"  # [PipelineUpdate]

    def __init__(self):
        super(Pipeline, self).__init__()

        self._eventLoop: Optional[asyncio.AbstractEventLoop] = None

        self._operators: List[Operator] = list()

        self._connectionLookup: Dict[int, Connection] = dict()
        self._operatorLookup: Dict[int, Operator] = dict()

        self.sources: List[Source] = list()

        # Storage of removed operators and connections to restore
        self._operatorStorage: Dict[int, Operator] = dict()
        self._connectionStorage: Dict[int, Connection] = dict()

    def registerConnection(self, connection: Connection):
        self._connectionLookup[connection.id] = connection

    def registerOperator(self, operator: Operator):
        self._operators.append(operator)

        self._operatorLookup[operator.id] = operator

        if operator.isSource():
            self.sources.append(operator)

    def getOperator(self, opID: int) -> Optional[Operator]:
        return self._operatorLookup.get(opID, None)

    def getConnection(self, conID: int) -> Optional[Connection]:
        return self._connectionLookup.get(conID, None)

    def getAllOperators(self) -> List[Operator]:
        return self._operators

    def getAllConnections(self):
        return self._connectionLookup.values()

    def getSources(self) -> List[Source]:
        return self.sources

    def getOperatorCount(self) -> int:
        return len(self._operators)

    def getEventLoop(self) -> asyncio.AbstractEventLoop:
        return self._eventLoop

    def removeOperator(self, opID: int):
        op = self.getOperator(opID)

        if op is None:
            return

        self._operatorLookup.pop(opID)
        self._operators.remove(op)

        op.onRuntimeDestroy()

        if op.isSource():
            self.sources.remove(op)

        # Remove all connections from this operator

        allCons: List[Connection] = list()
        for sockIn in op.inputs:
            allCons.extend(sockIn.getConnections())
        for sockOut in op.outputs:
            allCons.extend(sockOut.getConnections())

        for con in allCons:
            self.removeConnection(con.id)

    def removeConnection(self, conID: int):
        con = self.getConnection(conID)

        if con is None:
            return

        self._connectionLookup.pop(conID)

        con.input.removeConnection(con)
        con.output.removeConnection(con)

    def validate(self) -> (bool, str):
        if len(self.sources) == 0:
            return False, "No sources!"

        return True, ""

    def createRuntime(self, eventLoop: asyncio.AbstractEventLoop):
        self._eventLoop = eventLoop

        for operator in self.getAllOperators():
            operator.onRuntimeCreate(eventLoop)

    def shutdown(self):
        for operator in self.getAllOperators():
            operator.onRuntimeDestroy()

    def describe(self):
        print("--- PIPELINE ---")

        for op in self._operators:
            inString = ""
            outString = ""

            for i in op.inputs:
                for c in i.getConnections():
                    if len(inString) > 0:
                        inString += "\n"

                    inString += "    Socket[" + str(c.output.id) + "] at " \
                                + "Op[ID: " + str(c.output.op.id) \
                                + ", " + str(c.output.op.__class__.__name__) \
                                + "] --> Socket[" + str(i.id) + "], ConID: " + str(c.id)

            for i in op.outputs:
                for c in i.getConnections():
                    if len(outString) > 0:
                        outString += "\n"

                    outString += "    " + "Socket[" + str(i.id) \
                                 + "] --> " + "Socket[" + str(c.input.id) + "] at " \
                                 + "Op[ID: " + str(c.input.op.id) \
                                 + ", " + str(c.input.op.__class__.__name__) + "], ConID: " + str(c.id)

            if len(inString) > 0:
                inString = "\n" + inString

            if len(outString) > 0:
                outString = "\n" + outString

            print("Op[ID: " + str(op.id) + ", " + str(op.__class__.__name__) + "]" + inString + outString)

        # -----

        print("\n_Sources_")

        sources = ""

        for source in self.sources:
            if len(sources) > 0:
                sources += ", "
            sources += str(source.__class__.__name__)

        print(sources)

    # ----------------------- Storage Operations -----------------------

    def fetchOperatorFromStorage(self, opID: int) -> Optional[Operator]:
        return self._operatorStorage.get(opID, None)

    def fetchConnectionFromStorage(self, conID: int) -> Optional[Connection]:
        return self._connectionStorage.get(conID, None)

    def addOperatorToStorage(self, operator: Operator):
        self._operatorStorage[operator.id] = operator

    def addConnectionToStorage(self, connection: Connection):
        self._connectionStorage[connection.id] = connection

    def removeOperatorFromStorage(self, operator: Operator):
        self._operatorStorage.pop(operator.id, None)

    def removeConnectionFromStorage(self, connection: Connection):
        self._connectionStorage.pop(connection.id, None)
