from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict

from spe.common.serialization.jsonSerialization import fastSerializeToJSONBytes
from spe.runtime.monitor.dataProtocol import createOperatorData, createMessageBrokerData
from spe.runtime.monitor.dataProtocol import createConnectionData

if TYPE_CHECKING:
    from spe.runtime.debugger.history.pipelineHistoryBranch import PipelineHistoryBranch


class SocketTuple(ABC):
    def __init__(self, onSendCallback):
        self._onSendCallback = onSendCallback

    def onSend(self):
        if self._onSendCallback is not None:
            self._onSendCallback(self)

    @abstractmethod
    def getData(self) -> bytes | None:  # None = message is dropped
        pass


class OperatorSocketTuple(SocketTuple):
    def __init__(self, onSendCallback, operator):
        super(OperatorSocketTuple, self).__init__(onSendCallback)

        self.operator = operator

    def getData(self) -> bytes | None:
        return createOperatorData([self.operator])


class ConnectionSocketTuple(SocketTuple):
    def __init__(self, onSendCallback, connection):
        super(ConnectionSocketTuple, self).__init__(onSendCallback)

        self.connection = connection

    def getData(self) -> bytes | None:
        return createConnectionData([self.connection])


class MessageBrokerSocketTuple(SocketTuple):
    def __init__(self, onSendCallback, operators):
        super(MessageBrokerSocketTuple, self).__init__(onSendCallback)

        self.operators = operators

    def getData(self) -> bytes | None:
        return createMessageBrokerData(self.operators)


class DebugStepGetterSocketTuple(SocketTuple):
    def __init__(self, dataGetter, onSendCallback, currentStep, undo):
        super(DebugStepGetterSocketTuple, self).__init__(onSendCallback)

        self._dataGetter = dataGetter
        self.step = currentStep
        self.undo = undo

    def getData(self) -> bytes | None:
        return self._dataGetter(self.step, self.undo)


class HistoryBranchUpdateSocketTuple(SocketTuple):
    def __init__(self, onSendCallback, branch: PipelineHistoryBranch):
        super(HistoryBranchUpdateSocketTuple, self).__init__(onSendCallback)

        self.branches: Dict[int, PipelineHistoryBranch] = dict()
        self.addBranch(branch)

    def addBranch(self, branch: PipelineHistoryBranch):
        self.branches[branch.id] = branch

    def getData(self) -> bytes | None:
        data = {"cmd": "debHGUpdate"}

        updates = []

        for branch in self.branches.values():
            stepCount = branch.getStepCount()

            updates.append({"branchID": branch.id,
                            "startTime": branch.getFirstStep().time if stepCount > 0 else 0,
                            "endTime": branch.getLastStep().time if stepCount > 0 else 0,
                            "stepCount": branch.getStepCount(),
                            "stepOffset": branch.stepIDOffset})

        data["updates"] = updates

        return fastSerializeToJSONBytes(data)


class GenericSocketTuple(SocketTuple):
    def __init__(self, data, onSendCallback):
        super(GenericSocketTuple, self).__init__(onSendCallback)

        self._data = data

    def getData(self) -> bytes | None:
        return self._data

    def setData(self, data):
        self._data = data


class GenericGetterSocketTuple(SocketTuple):
    def __init__(self, dataGetter, onSendCallback):
        super(GenericGetterSocketTuple, self).__init__(onSendCallback)

        self._dataGetter = dataGetter

    def getData(self) -> bytes | None:
        return self._dataGetter()
