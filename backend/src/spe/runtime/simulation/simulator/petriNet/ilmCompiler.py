import json
import os.path
import time
from typing import Tuple, List, Dict

from analysis.costModel.configurations.costModelOpSetups import OpInputDataFeature, OpParamFeature
from analysis.costModel.costModel import CostModel, CostModelVariant, CostModelTarget, CostModelEnv
from spe.pipeline.operators.base.operators.windows.tumblingWindowCount import TumblingWindowCount
from spe.pipeline.operators.operator import Operator
from spe.pipeline.pipeline import Pipeline
from spe.pipeline.socket import Socket
from spe.runtime.simulation.simulationDummyData import SimulationDummyData
from spe.runtime.simulation.simulator.sourceConfig.simulationSourceConfig import SimulationSourceConfig


class IlmCompiler:
    def __init__(self, pipeline: Pipeline, realOpNames: Dict[str, str], costModelPath: str):
        self.pipeline = pipeline
        self.opNameLookup = realOpNames
        self.costModelPath = costModelPath

    def compile(self, duration: float, sourceCfgs: json, outputPath: str):
        # Convert the pipeline into the intermediate language model

        # --------- Base Data ---------

        ilm = {"name": "StreamVizzard ILM", "timestamp": int(time.time()), "duration": duration * 1000}

        # --------- Operators ---------

        components = []

        for op in self.pipeline.getAllOperators():
            if op.isSource():
                continue

            # Inputs & Outputs

            ins = []
            outs = []

            for inSock in op.inputs:
                if not inSock.hasConnections():
                    continue

                ins.append({"id": self._getPinID(op, inSock)})

            for outSock in op.outputs:
                if not outSock.hasConnections():
                    continue

                dataFunc = None

                # If op has no input pin we can not generate a data function
                if len(ins) > 0:  # TODO: Generate data transfer function based on the dataTransferFunc from the CostModel
                    dataFunc = "$" + ins[0]["id"]

                outs.append({"id": self._getPinID(op, outSock), "dataFunction": dataFunc})

            data = self._createBaseComponentData(op)

            data["inputPins"] = ins
            data["outputPins"] = outs

            components.append(data)

        ilm["components"] = components

        # --------- Sources ---------

        sources = []

        for source in self.pipeline.getSources():
            data: dict = self._createBaseComponentData(source)

            sourceCfg = SimulationSourceConfig.createConfig(source, sourceCfgs, self.costModelPath)

            data["executionFunction"] = {"meanValue": 1000 * sourceCfg.rate, "stdDev": 0, "maxError": 0}

            # Outputs

            producedData = sourceCfg.data.getDataVariations()

            outs = []

            for outID in range(len(source.outputs)):
                outSock = source.outputs[outID]

                if not outSock.hasConnections():
                    continue

                results = []

                socketData: List[Tuple[float, SimulationDummyData]] = producedData[outID]

                for elm in socketData:
                    results.append({"value": elm[1].inputData, "outputSize": elm[1].dataSize, "probability": elm[0]})

                outs.append({"id": self._getPinID(source, outSock), "results": results})

            data["outputPins"] = outs

            sources.append(data)

        ilm["sources"] = sources

        # --------- Connections ---------

        connections = []

        for op in self.pipeline.getAllOperators():
            for outSocks in op.outputs:
                for con in outSocks.getConnections():
                    connections.append({"source": self._getPinID(op, con.output, True),
                                        "target": self._getPinID(con.input.op, con.input, True),
                                        "transferTime": 1})  # For single node execution transfer time can be neglected

        ilm["connections"] = connections

        # Write the file

        fileName = os.path.join(outputPath, "ilm.json")

        os.makedirs(os.path.dirname(fileName), exist_ok=True)
        with open(fileName, "w") as f:
            f.write(json.dumps(ilm))

    def _getOpName(self, op: Operator) -> str:
        return self.opNameLookup.get(str(op.id), op.__class__.__name__)

    def _getPinID(self, op: Operator, socket: Socket, includeOp: bool = False):
        prefix = ""

        if includeOp:
            prefix = self._getOpName(op) + "__" + str(op.id) + "."

        if socket.inSocket:
            return prefix + "IN_" + str(socket.id)
        else:
            return prefix + "OUT_" + str(socket.id)

    def _createBaseComponentData(self, op: Operator):
        # Base

        data: dict = {
            "id": str(op.id),
            "name": self._getOpName(op),
            "parameters": [],
            "executionFunction": {
                "meanValue": 1,
                "stdDev": 0,
                "maxError": 0
            },
            "outputSize": 0}

        # Add operator specific settings

        settings = []

        if isinstance(op, TumblingWindowCount):
            settings.append({"key": "collect", "value": op.getData()["value"]})
            data["outputSize"] = "$" + self._getPinID(op, op.getInput(0)) + " * " + str(op.getData()["value"])

        data["settings"] = settings

        cm: CostModel = CostModel.load(type(op), self.costModelPath)

        if cm is None:
            return data

        # Operator Params

        exTimeVariant = cm.getVariant(CostModelEnv.SV_CPU, CostModelTarget.EXECUTION_TIME)
        if exTimeVariant is None:
            return data

        params = []

        for feature in exTimeVariant.features:
            if isinstance(feature, OpInputDataFeature):
                continue

            feat: OpParamFeature = feature

            params.append({"name": feature.name,
                           "value": feat.retriever(op)})

        data["parameters"] = params

        # Cost & Data Functions

        data["executionFunction"] = {"meanValue": self._retrieveFormula(op, exTimeVariant),
                                     "stdDev": exTimeVariant.rmse,
                                     "maxError": exTimeVariant.maxError}

        dataSizeVariant = cm.getVariant(CostModelEnv.SV_CPU, CostModelTarget.OUTPUT_SIZE)
        if dataSizeVariant is not None:
            data["outputSize"] = self._retrieveFormula(op, dataSizeVariant)

        return data

    def _retrieveFormula(self, operator: Operator, model: CostModelVariant):
        formula = model.getFormula().split("=", 1)[1].strip()

        for param in model.features:
            if isinstance(param, OpInputDataFeature):
                inSock = operator.getInput(param.socketID)
                sockedID = self._getPinID(operator, inSock)

                formula = formula.replace(param.name, "$" + sockedID)
            elif isinstance(param, OpParamFeature):
                formula = formula.replace(param.name, "@" + param.name)

        return formula
