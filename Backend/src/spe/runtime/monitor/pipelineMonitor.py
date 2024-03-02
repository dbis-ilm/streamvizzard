import json
import threading
import time
from threading import Thread
from typing import Dict, Optional

from config import MONITORING_UPDATE_INTERVAL
from network.server import ServerManager
from network.socketTuple import SocketTuple, OperatorSocketTuple, HeatmapSocketTuple, ConnectionSocketTuple, \
    MessageBrokerSocketTuple


class PipelineMonitor:
    def __init__(self, runtimeManager, serverManager: ServerManager):
        from spe.runtime.monitor.heatmap import Heatmap
        from spe.pipeline.operators.operator import Operator
        from spe.pipeline.connection import Connection

        self.runtimeManager = runtimeManager
        self.serverManager = serverManager
        self._heatmap = Heatmap()

        self._heatmapSendState: Optional[HeatmapSocketTuple] = None

        self._thread = Thread(target=self._threadFunction, daemon=True)
        self._executeThread = True
        self._thread.start()

        self._updatedOperatorLock = threading.Lock()
        self._updatedOperators: Dict[Operator, Operator] = dict()
        self._operatorSendState: Dict[Operator, OperatorSocketTuple] = dict()

        self._updateConnectionLock = threading.Lock()
        self._updatedConnections: Dict[Connection, Connection] = dict()
        self._connectionSendState: Dict[Connection, ConnectionSocketTuple] = dict()

        self._updateMessageBrokerLock = threading.Lock()
        self._messageBrokerSendState: Dict[Operator, bool] = dict()
        self._messageBrokerTuple: Optional[MessageBrokerSocketTuple] = None

    def reset(self):
        self._heatmap.changeType(0)

        self._updatedOperators.clear()
        self._updatedConnections.clear()
        self._connectionSendState.clear()
        self._operatorSendState.clear()
        self._messageBrokerSendState.clear()

    def onTupleProcess(self, operator):
        # Register operator for update

        with self._updatedOperatorLock:
            self._updatedOperators[operator] = operator

    def onOperatorError(self, operator, errorMsg: str):
        # Send error message independent of pipeline state (errors might occur on startup)

        self.serverManager.sendSocketData(json.dumps({"cmd": "opError", "op": operator.id, "error": errorMsg}))

    def onTupleTransmitted(self, connection):
        # Register connection for update

        with self._updateConnectionLock:
            self._updatedConnections[connection] = connection

    def onOpMessageQueueChanged(self, operator):
        with self._updateMessageBrokerLock:
            if operator not in self._messageBrokerSendState:
                self._messageBrokerSendState[operator] = True

                if self._messageBrokerTuple is None:
                    self._messageBrokerTuple = MessageBrokerSocketTuple(self._onMessageBrokerTupleSend, operator)
                    self.serverManager.sendSocketData(self._messageBrokerTuple)
                else:
                    self._messageBrokerTuple.addOperator(operator)

    def flushMonitorData(self):
        # Forces new data tuples to be created on next op/con update
        self._operatorSendState.clear()
        self._connectionSendState.clear()

    def _threadFunction(self):
        while self._executeThread:
            time.sleep(MONITORING_UPDATE_INTERVAL)

            self._sendMonitorData()

    def _sendMonitorData(self):
        if not self.runtimeManager.isRunning():
            return

        from spe.runtime.monitor.dataProtocol import createHeatmapData

        # TODO: BATCH MESSAGES TOGETHER?

        # SEND UPDATED OPERATORS

        with self._updatedOperatorLock:
            for operator in self._updatedOperators:
                if operator.getMonitor().isStatsEnabled() or operator.getMonitor().isDataEnabled():
                    elm = self._operatorSendState.get(operator, None)

                    if elm is None:
                        elm = OperatorSocketTuple(self._onOpTupleSend, operator)
                        self._operatorSendState[operator] = elm
                        self.serverManager.sendSocketData(elm)
                    else:
                        ...  # Not required since getData call with get most recent operator data

            hasNewData = len(self._updatedOperators) > 0
            self._updatedOperators.clear()

        # SEND UPDATED CONNECTIONS

        with self._updateConnectionLock:
            for connection in self._updatedConnections:
                elm = self._connectionSendState.get(connection, None)

                if elm is None:
                    elm = ConnectionSocketTuple(self._onConnectionTupleSend, connection)
                    self._connectionSendState[connection] = elm
                    self.serverManager.sendSocketData(elm)
                else:
                    ...  # Not required since getData call with get most recent connection data

            self._updatedConnections.clear()

        # CALCULATE AND SEND HEATMAP

        if hasNewData and self._heatmap.isRequested():
            heatmap = self._heatmap.calculate(self.runtimeManager.getPipeline())

            if heatmap is not None and heatmap.hasData():
                if self._heatmapSendState is None:
                    self._heatmapSendState = HeatmapSocketTuple(createHeatmapData(heatmap), self._onHMTupleSend)
                    self.serverManager.sendSocketData(self._heatmapSendState)
                else:
                    self._heatmapSendState.setData(createHeatmapData(heatmap))

    def _onOpTupleSend(self, st: OperatorSocketTuple):
        self._operatorSendState.pop(st.operator, None)

    def _onConnectionTupleSend(self, st: ConnectionSocketTuple):
        self._connectionSendState.pop(st.connection, None)

    def _onMessageBrokerTupleSend(self, st: MessageBrokerSocketTuple):
        with self._updateMessageBrokerLock:
            self._messageBrokerSendState.clear()
            self._messageBrokerTuple = None

    def _onHMTupleSend(self, st: SocketTuple):
        self._heatmapSendState = None

    def setHeatmapType(self, hmType):
        self._heatmap.changeType(hmType)
