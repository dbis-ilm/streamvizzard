from __future__ import annotations
import logging
import traceback
from typing import Dict, Optional, TYPE_CHECKING

from config import VERSION
from spe.pipeline.operators.operatorDB import getOperatorByPath
from utils.svResult import SvResult
from utils.utils import printWarning

from spe.pipeline.pipeline import Pipeline
from spe.pipeline.connection import Connection

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator


class PipelineManager:
    @staticmethod
    def createPipeline(data: Dict) -> PipelineCreationResult:
        pipeline = Pipeline(data.get("uuid", None))

        ops = data["operators"]
        cons = data["connections"]

        # Parse and add Operators
        for op in ops:
            PipelineManager.parseOperator(pipeline, op)

        # Parse and add Connections

        for con in cons:
            PipelineManager.parseConnection(pipeline, con)

        err = pipeline.validate()

        if err is not None:
            return PipelineCreationResult.error(err)

        return PipelineCreationResult(pipeline=pipeline)

    @staticmethod
    def createPipelineFromUISaveFile(data: Dict) -> PipelineCreationResult:
        cfg = PipelineManager._parseUISaveFile(data)

        return PipelineManager.createPipeline(cfg)

    @staticmethod
    def parseOperator(pipeline: Pipeline, opData: Dict) -> Optional[Operator]:
        opID = opData["id"]
        opDefinition = str(opData["definition"])
        opUUID = opData["uuid"]

        opClass: Operator = getOperatorByPath(opDefinition)

        if opClass is None:
            printWarning("ERROR: No class found for " + opDefinition)

            return None

        try:
            # noinspection PyCallingNonCallable
            operator: Operator = opClass(opID)

            operator.uuid = opUUID

            operator.setData(opData["params"])
        except Exception:
            operator: Optional[Operator] = None

            logging.log(logging.ERROR, traceback.format_exc())

        if operator is None:
            return None

        if "config" in opData:
            config = opData["config"]

            operator.setMonitorData(config.get("monitor"))
            operator.setBreakpointData(config.get("breakpoints"))

        if operator is None:
            return None

        pipeline.registerOperator(operator)

        return operator

    @staticmethod
    def parseConnection(pipeline: Pipeline, data: Dict) -> Optional[Connection]:
        conID = data["id"]

        inputOp = pipeline.getOperator(data["inputOp"])  # Operator with the "input" socket

        if inputOp is None:
            return None

        outputOp = pipeline.getOperator(data["outputOp"])  # Operator with the "output" socket

        if outputOp is None:
            return None

        inputSocket = inputOp.getInput(data["inputSocket"])

        if inputSocket is None:
            return None

        outputSocket = outputOp.getOutput(data["outputSocket"])

        if outputSocket is None:
            return None

        newCon = Connection.create(conID, inputSocket, outputSocket)
        pipeline.registerConnection(newCon)

        return newCon

    @staticmethod
    def _parseUISaveFile(data: Dict):
        """ Converts a pipeline storage file used in the UI to a representation the server can parse with createPipeline().
         This skips monitor display information as well as breakpoints! """

        pipelineData = data["pipeline"]

        for op in pipelineData["operators"]:
            op["config"] = {"monitor": {"enabled": op["showData"]}}

        return pipelineData

    @staticmethod
    def generateUISaveFile(pipeline: Pipeline) -> Dict:
        """
        Generates a save file used by the UI based on the pipeline.
        This will not be able to include UI-specific settings, but only the pipeline structure & data.
        """

        ops = []
        cons = []

        for op in pipeline.getAllOperators():
            data = op.exportOperatorData()
            data["svVersion"] = VERSION

            ops.append(data)

        for con in pipeline.getAllConnections():
            cons.append({"id": con.id, "inputOp": con.input.op.id, "inputSocket": con.input.id,
                         "outputOp": con.output.op.id, "outputSocket": con.output.id})

        data = {"svVersion": VERSION, "pipeline": {"operators": ops, "connections": cons}}

        return data


class PipelineCreationResult(SvResult):
    def __init__(self, pipeline: Optional[Pipeline] = None, error: Optional[str] = None):
        super().__init__(error)

        self.pipeline = pipeline
