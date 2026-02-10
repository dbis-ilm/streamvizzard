from __future__ import annotations
import asyncio
import uuid
from typing import List, Dict, Optional, TYPE_CHECKING, Iterator, Set

from spe.pipeline.connection import Connection

from spe.common.iEventEmitter import IEventEmitter

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.pipeline.operators.source import Source


class Pipeline(IEventEmitter):
    EVENT_PIPELINE_PRE_UPDATED = "PrePipeUpdated"  # [PipelineUpdate]
    EVENT_PIPELINE_UPDATED = "PipeUpdated"  # [PipelineUpdate]

    def __init__(self, pipelineID: Optional[str] = None):
        super(Pipeline, self).__init__()

        self.uuid = str(uuid.uuid4().hex) if (pipelineID is None or len(pipelineID) == 0) else pipelineID

        self._eventLoop: Optional[asyncio.AbstractEventLoop] = None

        self._operators: List[Operator] = list()

        self._connectionLookup: Dict[int, Connection] = dict()
        self._operatorLookup: Dict[int, Operator] = dict()

        self.sources: List[Source] = list()

        # Storage of removed operators and connections to restore
        self._operatorStorage: Dict[int, Operator] = dict()
        self._connectionStorage: Dict[int, Connection] = dict()

    def registerConnection(self, connection: Connection) -> bool:
        if connection.id in self._connectionLookup:
            return False

        self._connectionLookup[connection.id] = connection

        return True

    def registerOperator(self, operator: Operator) -> bool:
        if operator.id in self._operatorLookup:
            return False

        self._operators.append(operator)

        self._operatorLookup[operator.id] = operator

        if operator.isSource():
            self.sources.append(operator)

        return True

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

    def getSinks(self) -> List[Operator]:
        """ Collects all operators that do not have any output operators connected. """

        sinks = []

        for op in self.getAllOperators():
            if len(op.getNeighbours(False, True)) == 0:
                sinks.append(op)

        return sinks

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

    def validate(self) -> Optional[str]:
        if len(self.sources) == 0:
            return "Pipeline has no sources!"

        # Check cyclic connections

        visitedStack: Set[int] = set()
        handledOps: Set[int] = set()

        def visitOp(currentOp: Operator) -> bool:
            handledOps.add(currentOp.id)
            visitedStack.add(currentOp.id)

            for outSock in currentOp.outputs:
                for c in outSock.getConnections():
                    nextOp = c.input.op

                    if nextOp.id not in handledOps:
                        if not visitOp(nextOp):
                            return False

                    elif nextOp.id in visitedStack:
                        return False

            visitedStack.remove(currentOp.id)

            return True

        for op in self.getAllOperators():
            if op.id in handledOps:
                continue

            if not visitOp(op):
                return "Pipeline contains cyclic connections!"

        # Verify that all parent/children constraints are fulfilled

        for op in self.getAllOperators():
            if op.allowedParents is not None:
                for parent in op.getNeighbours(True, False):

                    isAllowed = False

                    for allowed in op.allowedParents:
                        if isinstance(parent, allowed):
                            isAllowed = True

                            break

                    if not isAllowed:
                        return f"Operator {parent.getUniqueName()} not allowed as parent for {op.getUniqueName()}!"

            if op.allowedChildren is not None:
                for child in op.getNeighbours(False, True):

                    isAllowed = False

                    for allowed in op.allowedChildren:
                        if isinstance(child, allowed):
                            isAllowed = True

                            break

                    if not isAllowed:
                        return f"Operator {child.getUniqueName()} not allowed as child for {op.getUniqueName()}!"

        return None

    def createRuntime(self, eventLoop: asyncio.AbstractEventLoop) -> bool:
        self._eventLoop = eventLoop

        hasError = False

        for operator in self.getAllOperators():
            try:
                operator.onRuntimeCreate(eventLoop)
            except Exception:
                operator.onExecutionError()

                hasError = True

        return not hasError

    def shutdown(self):
        for operator in self.getAllOperators():
            try:
                operator.onRuntimeDestroy()
            except Exception:
                operator.onExecutionError()

    def iterateTopological(self) -> Iterator[Operator]:
        """ Returns an iterator that visits all operators in an order that
        every input of an operator is visited before the actual operator. """

        handledOps: Set[int] = set()

        def ensureInput(op: Operator) -> Iterator[Operator]:
            if op.id in handledOps:
                return

            handledOps.add(op.id)

            inputs = op.getNeighbours(True, False)

            for inp in inputs:
                yield from ensureInput(inp)

            yield op

        for operator in self.getAllOperators():
            yield from ensureInput(operator)

    def iterateReversedTopological(self) -> Iterator[Operator]:
        """ Returns an iterator that visits all operators in an order that
        every output of an operator is visited before the actual operator. """

        handledOps: Set[int] = set()

        def ensureOutput(op: Operator) -> Iterator[Operator]:
            if op.id in handledOps:
                return

            handledOps.add(op.id)

            outputs = op.getNeighbours(False, True)

            for oup in outputs:
                yield from ensureOutput(oup)

            yield op

        for operator in self.getAllOperators():
            yield from ensureOutput(operator)

    def describe(self):
        print(f"--- PIPELINE {self.uuid} ---")

        orderedOps = sorted(self._operators, key=lambda x: x.id)

        for op in orderedOps:
            inString = ""
            outString = ""

            for i in op.inputs:
                for c in i.getConnections():
                    if len(inString) > 0:
                        inString += "\n"

                    inString += "    Socket[" + str(c.output.id) + "] at " \
                                + "Op[ID: " + str(c.output.op.id) \
                                + ", " + c.output.op.getName() \
                                + "] --> Socket[" + str(i.id) + "], ConID: " + str(c.id)

            for i in op.outputs:
                for c in i.getConnections():
                    if len(outString) > 0:
                        outString += "\n"

                    outString += "    " + "Socket[" + str(i.id) \
                                 + "] --> " + "Socket[" + str(c.input.id) + "] at " \
                                 + "Op[ID: " + str(c.input.op.id) \
                                 + ", " + c.input.op.getName() + "], ConID: " + str(c.id)

            if len(inString) > 0:
                inString = "\n" + inString

            if len(outString) > 0:
                outString = "\n" + outString

            print("Op[ID: " + str(op.id) + ", " + op.getName() + "]" + inString + outString)

        # -----

        print("\n_Sources_")

        sources = ""

        orederedSources = sorted(self.sources, key=lambda x: x.id)

        for source in orederedSources:
            if len(sources) > 0:
                sources += ", "
            sources += source.getName()

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
