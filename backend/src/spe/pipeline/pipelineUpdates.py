from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Optional

from spe.pipeline.connection import Connection
from spe.pipeline.operators.operator import Operator
from spe.pipeline.pipeline import Pipeline
from spe.pipeline.pipelineManager import PipelineManager
from utils.utils import printWarning


class PipelineUpdate(ABC):
    def __init__(self, updateID: int):
        self.pipeline: Optional[Pipeline] = None
        self.updateID = updateID

    def updatePipeline(self, pipeline: Pipeline):
        self.pipeline = pipeline

        self.execute()

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

    def redo(self):
        self.execute()

    def isTracked(self):  # If this update is tracked inside the history
        return True

    def isLogicalChange(self):  # If this update describes an operator/connection change (no meta or ui updates)
        return True

    @staticmethod
    def parse(updateData: Dict, updateID: int) -> Optional[PipelineUpdate]:
        tp = updateData["type"]

        if tp == "opAdded":
            return OperatorAddedPU.parse(updateID, updateData)
        elif tp == "opRemoved":
            return OperatorRemovedPU.parse(updateID, updateData)
        elif tp == "opDataUpdated":
            return OperatorDataUpdatedPU.parse(updateID, updateData)
        elif tp == "opMetaUpdated":
            return OperatorMetaDataUpdatedPU.parse(updateID, updateData)
        elif tp == "conAdded":
            return ConnectionAddedPU.parse(updateID, updateData)
        elif tp == "conRemoved":
            return ConnectionRemovedPU.parse(updateID, updateData)
        elif tp == "generic":
            return GenericUpdatePU(updateID)

        return None


class OperatorAddedPU(PipelineUpdate):
    def __init__(self, updateID: int, opID: int, opData: Dict):
        super().__init__(updateID)

        self.opID = opID
        self.opData = opData

    def execute(self):
        # Check if this operator already exists in storage and retrieve it.
        # The operator exists, if an operator deletion is undone in editor.

        newOp = self.pipeline.fetchOperatorFromStorage(self.opID)

        if newOp is None:
            newOp = PipelineManager.parseOperatorAndConnections(self.pipeline, self.opData, None)
            newOp.onRuntimeCreate(self.pipeline.getEventLoop())
        else:
            OperatorAddedPU.restoreOperator(self.pipeline, self.opID)

    def undo(self):
        OperatorRemovedPU.removeOperator(self.pipeline, self.opID)

    def redo(self):
        OperatorAddedPU.restoreOperator(self.pipeline, self.opID)

    @staticmethod
    def restoreOperator(pipeline: Pipeline, opID: int) -> Optional[Operator]:
        opToRestore = pipeline.fetchOperatorFromStorage(opID)

        if opToRestore is None:
            printWarning("Operator to restore [" + str(opID) + "] not found!")
            return None

        pipeline.registerOperator(opToRestore)
        opToRestore.onRuntimeCreate(pipeline.getEventLoop())

        pipeline.removeOperatorFromStorage(opToRestore)

        return opToRestore

    @staticmethod
    def parse(updateID: int, data: Dict) -> OperatorAddedPU:
        return OperatorAddedPU(updateID, data["opID"], data["opData"])


class OperatorRemovedPU(PipelineUpdate):
    def __init__(self, updateID: int, opID: int):
        super().__init__(updateID)

        self.opID = opID

    def execute(self):
        OperatorRemovedPU.removeOperator(self.pipeline, self.opID)

    def undo(self):
        OperatorAddedPU.restoreOperator(self.pipeline, self.opID)

    @staticmethod
    def removeOperator(pipeline: Pipeline, opID: int):
        opToRemove = pipeline.getOperator(opID)

        if opToRemove is None:
            printWarning("Operator to remove [" + str(opID) + "] not found!")
            return

        pipeline.addOperatorToStorage(opToRemove)

        pipeline.removeOperator(opID)

    @staticmethod
    def parse(updateID: int, data: Dict) -> OperatorRemovedPU:
        return OperatorRemovedPU(updateID, data["opID"])


class OperatorDataUpdatedPU(PipelineUpdate):
    def __init__(self, updateID: int, opID: int, opUUID: str, opData: Dict, param: str):
        super().__init__(updateID)

        self.opID = opID
        self.opUUID = opUUID
        self.opData = opData
        self.param = param
        self._prevData = None

    def execute(self):
        op = self.pipeline.getOperator(self.opID)

        if op is None:
            printWarning("Operator to revert data [" + str(self.opID) + "] not found!")
            return

        self._prevData = op.getData()

        if op is not None:
            try:
                op.setData(self.opData)
                op.uuid = self.opUUID
            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())

    def undo(self):
        op = self.pipeline.getOperator(self.opID)

        if op is None:
            printWarning("Operator to revert data [" + str(self.opID) + "] not found!")
            return

        try:
            op.setData(self._prevData)
            # We currently do not undo uuid [not required]
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

    @staticmethod
    def parse(updateID: int, data: Dict) -> OperatorDataUpdatedPU:
        return OperatorDataUpdatedPU(updateID, data["opID"], data["opUUID"], data["opData"], data["ctrlKey"])


class OperatorMetaDataUpdatedPU(PipelineUpdate):
    def __init__(self, updateID: int, opID: int, metaData: Dict):
        super().__init__(updateID)

        self.opID = opID
        self.metaData = metaData

    def execute(self):
        op = self.pipeline.getOperator(self.opID)

        if op is not None:
            op.setMonitorData(self.metaData["monitor"])
            op.setBreakpointData(self.metaData["breakpoints"])

    def undo(self):
        ...  # Unused

    def isTracked(self):
        return False

    def isLogicalChange(self):
        return False

    @staticmethod
    def parse(updateID: int, data: Dict) -> OperatorMetaDataUpdatedPU:
        return OperatorMetaDataUpdatedPU(updateID, data["opID"], data["metaData"])


class ConnectionAddedPU(PipelineUpdate):
    def __init__(self, updateID: int, conID: int, outOpID: int, inOpID: int, outSocketID: int, inSocketID: int):
        super().__init__(updateID)

        self.conID = conID
        self.outOpID = outOpID
        self.inOpID = inOpID
        self.outSocketID = outSocketID
        self.inSocketID = inSocketID

    def execute(self):
        # Check if this connection already exists in storage and retrieve it.
        # The connection exists, if a connection deletion is undone in editor.

        newCon = self.pipeline.fetchConnectionFromStorage(self.conID)

        if newCon is None:
            inOp = self.pipeline.getOperator(self.inOpID)
            outOp = self.pipeline.getOperator(self.outOpID)

            if inOp is None or outOp is None:
                return

            inSocket = inOp.getInput(self.inSocketID)
            outSocket = outOp.getOutput(self.outSocketID)

            if inSocket is None or outSocket is None:
                return

            newCon = Connection.create(self.conID, inSocket, outSocket)
            self.pipeline.registerConnection(newCon)
        else:
            ConnectionAddedPU.restoreConnection(self.pipeline, self.conID)

    def undo(self):
        ConnectionRemovedPU.removeConnection(self.pipeline, self.conID)

    def redo(self):
        ConnectionAddedPU.restoreConnection(self.pipeline, self.conID)

    @staticmethod
    def restoreConnection(pipeline: Pipeline, conID: int) -> Optional[Connection]:
        conToRestore = pipeline.fetchConnectionFromStorage(conID)

        if conToRestore is None:
            printWarning("Connection to restore [" + str(conID) + "] not found!")
            return None

        prevInSocket = conToRestore.input
        prevOutSocket = conToRestore.output

        # Fetch current operator and socket data and check if operators/sockets exists currently

        inOp = pipeline.getOperator(prevInSocket.op.id)
        outOp = pipeline.getOperator(prevOutSocket.op.id)

        if inOp is None:
            printWarning("In operator [" + str(prevInSocket.op.id) + "] not found!")
            return None

        if outOp is None:
            printWarning("In operator [" + str(prevOutSocket.op.id) + "] not found!")
            return None

        newInSocket = inOp.getInput(prevInSocket.id)
        newOutSocket = outOp.getOutput(prevOutSocket.id)

        if newInSocket is None:
            printWarning("In socket [" + str(prevInSocket.id) + "] not found!")
            return None

        if newOutSocket is None:
            printWarning("In socket [" + str(prevOutSocket.id) + "] not found!")
            return None

        # Update new data and register connection

        conToRestore.input = newInSocket
        conToRestore.output = newOutSocket

        conToRestore.input.addConnection(conToRestore)
        conToRestore.output.addConnection(conToRestore)

        pipeline.registerConnection(conToRestore)

        pipeline.removeConnectionFromStorage(conToRestore)

        return conToRestore

    @staticmethod
    def parse(updateID: int, data: Dict) -> ConnectionAddedPU:
        return ConnectionAddedPU(updateID, data["connectionID"], data["outOpID"], data["inOpID"], data["outSocketID"], data["inSocketID"])


class ConnectionRemovedPU(PipelineUpdate):
    def __init__(self, updateID: int, conID: int):
        super().__init__(updateID)

        self.conID = conID

    def execute(self):
        ConnectionRemovedPU.removeConnection(self.pipeline, self.conID)

    def undo(self):
        ConnectionAddedPU.restoreConnection(self.pipeline, self.conID)

    @staticmethod
    def removeConnection(pipeline: Pipeline, conID: int):
        conToRemove = pipeline.getConnection(conID)

        if conToRemove is None:
            printWarning("Connection to remove [" + str(conID) + "] not found!")
            return

        pipeline.addConnectionToStorage(conToRemove)

        pipeline.removeConnection(conID)

    @staticmethod
    def parse(updateID: int, data: Dict) -> ConnectionRemovedPU:
        return ConnectionRemovedPU(updateID, data["connectionID"])


class GenericUpdatePU(PipelineUpdate):
    def execute(self):
        pass

    def undo(self):
        pass

    def isLogicalChange(self):
        return False
