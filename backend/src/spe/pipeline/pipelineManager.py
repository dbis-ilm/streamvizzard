from __future__ import annotations
import logging
import traceback
import uuid
from typing import Dict, Optional, TYPE_CHECKING

from spe.pipeline.operators.operatorDB import getOperatorByPath
from utils.svResult import SvResult
from utils.utils import printWarning

from spe.pipeline.pipeline import Pipeline
from spe.pipeline.connection import Connection

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.pipeline.socket import Socket


class PipelineManager:
    @staticmethod
    def createPipeline(data: Dict) -> PipelineCreationResult:
        pipeline = Pipeline(data.get("uuid", None))

        # Stores all connection information for the sockets to be processed after all operators have been defined
        connectionBuffer: Dict[Socket, Dict] = dict()

        ops = data["operators"]

        # Parse and add Operators
        for op in ops:
            PipelineManager.parseOperatorAndConnections(pipeline, op, connectionBuffer)

        # Parse and add Connections

        for socket in connectionBuffer:
            cons = connectionBuffer[socket]

            PipelineManager._parseConnections(pipeline, socket, cons)

        err = pipeline.validate()

        if err is not None:
            return PipelineCreationResult.error(err)

        return PipelineCreationResult(pipeline=pipeline)

    @staticmethod
    def createPipelineFromUISaveFile(data: Dict) -> PipelineCreationResult:
        cfg = PipelineManager.parseUISaveFile(data)

        return PipelineManager.createPipeline(cfg)

    @staticmethod
    def parseOperatorAndConnections(pipeline: Pipeline, op: Dict, conBuffer: Optional[Dict[Socket, Dict]]) -> Optional[Operator]:
        operator = PipelineManager.parseOperator(op)

        if operator is None:
            return None

        pipeline.registerOperator(operator)

        PipelineManager.parseOperatorConnections(pipeline, operator, op, conBuffer)

        return operator

    @staticmethod
    def parseOperator(op: Dict) -> Optional[Operator]:
        opIdentifier = op["id"]

        opID = opIdentifier["id"]
        opPath = str(opIdentifier["path"])
        opUUID = opIdentifier["uuid"]

        opClass: Operator = getOperatorByPath(opPath)

        if opClass is None:
            printWarning("ERROR: No class found for " + opPath)

            return None

        try:
            # noinspection PyCallingNonCallable
            operator: Operator = opClass(opID)

            operator.uuid = opUUID

            operator.setData(op["data"])
        except Exception:
            operator: Optional[Operator] = None

            logging.log(logging.ERROR, traceback.format_exc())

        if operator is None:
            return None

        operator.setMonitorData(op["monitor"])
        operator.setBreakpointData(op["breakpoints"])

        return operator

    @staticmethod
    def parseOperatorConnections(pipeline: Pipeline, operator: Operator, op: Dict, conBuffer: Optional[Dict[Socket, Dict]]):
        # Parse sockets

        inputs = op["inputs"]
        outputs = op["outputs"]

        for inp in inputs:
            socketID = inp["socket"]
            connections = inp["connected"]

            socket = operator.getInput(socketID)

            if socket is None:
                printWarning("ERROR: No IN socket found for operator " + str(operator.id) + " at socketID " + str(socketID))

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
                printWarning("ERROR: No OUT socket found for operator " + str(operator.id) + " at socketID " + str(socketID))

                continue

            if conBuffer is not None:
                conBuffer[socket] = connections
            else:
                PipelineManager._parseConnections(pipeline, socket, connections)

    @staticmethod
    def _parseConnections(pipeline: Pipeline, socket: Socket, data: Dict):
        if len(data) == 0:
            return

        for c in data:
            otherSocketID = c["socket"]
            otherOpIdentifier = c["component"]
            connectionID = c["id"]

            otherOp = pipeline.getOperator(otherOpIdentifier["id"])

            if otherOp is None:
                printWarning("Operator " + str(otherOpIdentifier) + " not present in pipeline!")
                continue

            # Get connection if already exists
            connection = pipeline.getConnection(connectionID)

            # Create new connection if not
            if connection is None:
                if socket.inSocket:
                    newCon = Connection.create(connectionID, socket, otherOp.getOutput(otherSocketID))
                    pipeline.registerConnection(newCon)
                else:
                    newCon = Connection.create(connectionID, otherOp.getInput(otherSocketID), socket)
                    pipeline.registerConnection(newCon)

    @staticmethod
    def parseUISaveFile(config: Dict):
        """ Converts a pipeline storage file used in the UI to a representation the server can parse with createPipeline() """

        opLookup: Dict[int, Dict] = dict()

        pipelineData = config["pipeline"]
        nodes = pipelineData["graph"]["nodes"].values()

        # One iteration to set up all operators and sockets

        for node in nodes:
            inputs = []
            outputs = []

            for elem in node["inputs"]:
                inputs.append({"socket": len(inputs), "connected": [], "key": elem})

            for elem in node["outputs"]:
                outputs.append({"socket": len(outputs), "connected": [], "key": elem})

            op = {"id": {"id": node["id"], "path": None, "uuid": uuid.uuid4().hex}, "inputs": inputs, "outputs": outputs, "data": {}, "monitor": {}, "breakpoints": []}

            opLookup[node["id"]] = op

        # Fill in paths, data, and monitor of operators

        for op in pipelineData["op"]:
            opObj = opLookup[op["id"]]
            opObj["id"]["path"] = op["path"]
            opObj["id"]["uuid"] = op["uuid"]
            opObj["data"] = op["data"]
            opObj["monitor"] = op["monitor"]

        def _findOutSockByKey(opData, sockKey):
            for sock in opData["outputs"]:
                if sock["key"] == sockKey:
                    return sock["socket"]
            return None

        # Create connections between operators

        for node in nodes:
            thisOp = opLookup[node["id"]]

            if thisOp is None:
                continue

            # Connect inputs of operators (only need to consider inputs since each input is connected to an output
            # Required since UI connections don't have ID's, so incrementally assigning connection IDs is incorrect

            inSockID = 0
            for key, inp in node["inputs"].items():
                for con in inp["connections"]:
                    otherOp = opLookup[con["node"]]

                    if otherOp is None:
                        continue

                    # Find correct out socket ID by key
                    sockID = _findOutSockByKey(otherOp, con["output"])

                    if sockID is None:
                        continue

                    thisOp["inputs"][inSockID]["connected"].append({"socket": sockID, "component": otherOp["id"], "id": con["id"]})

                inSockID += 1

        return {"operators": [op for op in opLookup.values()]}

    @staticmethod
    def generateUISaveFile(pipeline: Pipeline) -> Dict:
        """
        Generates a save file used by the UI based on the pipeline.
        This will not be able to include UI-specific settings, but only the pipeline structure & data.
        """

        nodes = {}
        ops = []

        for op in pipeline.getAllOperators():
            data = op.exportOperatorData()

            inputs = {}
            conDataInputs = []

            for inp in data["inputs"]:
                connections = []

                for con in inp["connected"]:
                    connections.append({"node": con["component"]["id"], "output": "out" + str(con["socket"]), "id": con["id"]})

                inputs["in" + str(inp["socket"])] = {"connections": connections}
                conDataInputs.append({"id": "in" + str(inp["socket"]), "name": "Data"})

            outputs = {}
            conDataOutputs = []

            for outp in data["outputs"]:
                connections = []

                for con in outp["connected"]:
                    connections.append({"node": con["component"]["id"], "input": "in" + str(con["socket"]), "id": con["id"]})

                outputs["out" + str(outp["socket"])] = {"connections": connections}
                conDataOutputs.append({"id": "out" + str(outp["socket"]), "name": "Data"})

            ops.append({"id": data["id"]["id"], "path": data["id"]["path"], "uuid": data["id"]["uuid"],
                        "dName": op.getName(), "data": data["data"], "monitor": data["monitor"],
                        "breakPoints": data["breakpoints"], "conData": {"inputs": conDataInputs, "outputs": conDataOutputs}})

            nodes[op.id] = {"id": data["id"]["id"], "name": op.getName(), "position": [0, 0],
                            "inputs": inputs, "outputs": outputs}

        data = {"pipeline": {"graph": {"nodes": nodes}, "op": ops}}

        return data


class PipelineCreationResult(SvResult):
    def __init__(self, pipeline: Optional[Pipeline] = None, error: Optional[str] = None):
        super().__init__(error)

        self.pipeline = pipeline
