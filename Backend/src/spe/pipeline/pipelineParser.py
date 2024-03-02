import json
from typing import Dict, Optional

from spe.pipeline.operators import operatorDB
from spe.pipeline.operators.operator import Operator
from spe.pipeline.connection import Connection
from spe.pipeline.pipeline import Pipeline
from spe.pipeline.socket import Socket


class PipelineManager:
    @staticmethod
    def createPipeline(data: json) -> Pipeline:
        pipeline = PipelineManager.parsePipeline(data)

        return pipeline

    @staticmethod
    def parsePipeline(data: json) -> Optional[Pipeline]:
        pipeline = Pipeline()

        # Stores all connection information for the sockets to be processed after all operators have been defined
        connectionBuffer: Dict[Socket, json] = dict()

        ops = data["operators"]

        # Parse and add Operators
        for op in ops:
            PipelineManager.parseOperatorAndConnections(pipeline, op, connectionBuffer)

        # Parse and add Connections

        for socket in connectionBuffer:
            cons = connectionBuffer[socket]

            PipelineManager._parseConnections(pipeline, socket, cons)

        res, err = pipeline.validate()
        if not res:
            print("Parsing Pipeline returned error:\n" + err)
            return None

        return pipeline

    @staticmethod
    def parseOperatorAndConnections(pipeline: Pipeline, op: json, conBuffer: Optional[Dict[Socket, Dict]]) -> Optional[Operator]:
        operator = PipelineManager.parseOperator(pipeline, op)

        if operator is None:
            return

        PipelineManager.parseOperatorConnections(pipeline, operator, op, conBuffer)

        return operator

    @staticmethod
    def parseOperator(pipeline: Pipeline, op: json) -> Optional[Operator]:
        opIdentifier = op["id"]

        opID = opIdentifier["id"]
        opPath = str(opIdentifier["path"])

        opClass: Operator = operatorDB.getOperatorByPath(opPath)

        if opClass is None:
            print("ERROR: No class found for " + opPath)

            return None

        # noinspection PyCallingNonCallable
        operator: Operator = opClass(opID)

        operator.setData(op["data"])
        operator.setMonitorData(op["monitor"])
        operator.setBreakpointData(op["breakpoints"])

        pipeline.registerOperator(operator)

        return operator

    @staticmethod
    def parseOperatorConnections(pipeline: Pipeline, operator: Operator, op: json, conBuffer: Optional[Dict[Socket, Dict]]):
        # Parse sockets

        inputs = op["inputs"]
        outputs = op["outputs"]

        for inp in inputs:
            socketID = inp["socket"]
            connections = inp["connected"]

            socket = operator.getInput(socketID)

            if socket is None:
                print("ERROR: No IN socket found for operator " + str(operator.id) + " at socketID " + str(socketID))

                continue

            if conBuffer is not None:
                conBuffer[socket] = connections
            else:
                PipelineManager._parseConnections(pipeline, socket, connections)

        for inp in outputs:
            socketID = inp["socket"]
            connections = inp["connected"]

            socket = operator.getOutput(socketID)

            if socket is None:
                print("ERROR: No OUT socket found for operator " + str(operator.id) + " at socketID " + str(socketID))

                continue

            if conBuffer is not None:
                conBuffer[socket] = connections
            else:
                PipelineManager._parseConnections(pipeline, socket, connections)

    @staticmethod
    def _parseConnections(pipeline: Pipeline, socket: Socket, data: json):
        if len(data) == 0:
            return None

        for c in data:
            otherSocketID = c["socket"]
            otherOpIdentifier = c["component"]
            connectionID = c["id"]

            otherOp = pipeline.getOperator(otherOpIdentifier["id"])

            # Get connection if already exists
            connection = pipeline.getConnection(connectionID)

            # Create new connection if not
            if connection is None:
                if socket.inSocket:
                    Connection.create(pipeline, connectionID, socket, otherOp.getOutput(otherSocketID))
                else:
                    Connection.create(pipeline, connectionID, otherOp.getInput(otherSocketID), socket)
