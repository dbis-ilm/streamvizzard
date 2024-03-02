from __future__ import annotations
from typing import Set, List, TYPE_CHECKING

from spe.pipeline.operators.operator import Operator
from spe.runtime.structures.stream import Stream

if TYPE_CHECKING:
    from spe.pipeline.pipeline import Pipeline


class Clustering:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

        self.streamIdCounter = 0

        self.visited: Set[Operator] = set()

    def cluster(self):
        for s in self.pipeline.sources:
            self._calcCluster(s)

    def _calcCluster(self, startOp: Operator):
        if startOp in self.visited:
            return

        self.visited.add(startOp)

        if startOp.stream is None:
            newStream = Stream(self.streamIdCounter)
            self.streamIdCounter += 1

            self.pipeline.registerStream(newStream)

            newStream.registerOperator(startOp)

        stream = startOp.stream

        # Collect all out connected operators

        connectedOpsOUT: List[Operator] = list()

        for socket in startOp.outputs:
            for connection in socket.getConnections():
                connectedOpsOUT.append(connection.input.op)

        connectedOpCountOUT = len(connectedOpsOUT)

        # ---------- Assign streams for alle connections ----------

        # Each out connection need to be a new stream if (or):
        # - Operator is a Source
        # - Operator has multiple out connections
        # - Operator is PipelineBreaker

        if connectedOpCountOUT > 1 or startOp.pipelineBreaker or startOp.isSource():
            for connected in connectedOpsOUT:
                self._calcCluster(connected)

        # Trivial case: none/one input, one output, just add operator to stream

        elif connectedOpCountOUT == 1:
            childOp = connectedOpsOUT.pop()

            # Check the input count of the child operator

            connectedOpsIN: Set[Operator] = set()
            for socket in childOp.inputs:
                for connection in socket.getConnections():
                    connectedOpsIN.add(connection.output.op)

            connectedOpCountIN = len(connectedOpsIN)

            # We are the only input operator

            if connectedOpCountIN == 1:
                stream.registerOperator(childOp)

            self._calcCluster(childOp)
