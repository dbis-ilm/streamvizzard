from __future__ import annotations
import json
import threading
import time
from threading import Thread
from typing import Dict, Optional, TYPE_CHECKING

from network.socketTuple import SocketTuple, OperatorSocketTuple, HeatmapSocketTuple, ConnectionSocketTuple, \
    MessageBrokerSocketTuple
from spe.runtime.monitor.dataProtocol import createHeatmapData
from spe.runtime.monitor.pipelineDataAnalyzer import PipelineDataAnalyzer
from spe.common.runtimeService import RuntimeService
from streamVizzard import StreamVizzard

if TYPE_CHECKING:
    from network.server import ServerManager
    from spe.runtime.runtimeManager import RuntimeManager


class PipelineMonitor(RuntimeService):
    def __init__(self, runtimeManager: RuntimeManager, serverManager: ServerManager):
        super().__init__(runtimeManager, serverManager)

        from spe.runtime.monitor.heatmap import Heatmap
        from spe.pipeline.operators.operator import Operator
        from spe.pipeline.connection import Connection

        self._enabled = False  # Enabled = Sending data | False = Still tracking data (errors always send)

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
        self._messageBrokerUpdates: Dict[Operator, bool] = dict()
        self._messageBrokerTuple: Optional[MessageBrokerSocketTuple] = None

        self._pipelineAnalyzer: Optional[PipelineDataAnalyzer] = None

    def onPipelineStarting(self):
        if StreamVizzard.getConfig().MONITORING_TRACK_PIPELINE_STATS:
            self._pipelineAnalyzer = PipelineDataAnalyzer()
            self._pipelineAnalyzer.initialize(self.getPipeline())

    def onPipelineStopped(self):
        self._heatmap.changeType(0)

        self._updatedOperators.clear()
        self._updatedConnections.clear()
        self._messageBrokerUpdates.clear()

        self.flushMonitorData()

        if self._pipelineAnalyzer is not None:
            self._pipelineAnalyzer.finalize(self.getPipeline())

    def onTupleProcess(self, operator):
        if not self._shouldSendMonitorData():
            return

        # Register operator for update

        with self._updatedOperatorLock:
            self._updatedOperators[operator] = operator

    def onOperatorError(self, operator, errorMsg: Optional[str]):
        # Always send errors, also if monitor is disabled
        # Send error message independent of pipeline state (errors might occur on startup)

        self.serverManager.sendSocketData(json.dumps({"cmd": "opError", "op": operator.id, "error": errorMsg}))

    def onTupleTransmitted(self, connection):
        if not self._shouldSendMonitorData():
            return

        # Register connection for update

        with self._updateConnectionLock:
            self._updatedConnections[connection] = connection

    def onOpMessageQueueChanged(self, operator):
        if not self._shouldSendMonitorData():
            return

        with self._updateMessageBrokerLock:
            self._messageBrokerUpdates[operator] = True

    def flushMonitorData(self):
        # Forces new data tuples to be created on next op/con/broker update
        self._operatorSendState.clear()
        self._connectionSendState.clear()

        self._messageBrokerTuple = None
        self._heatmapSendState = None

    def changeConfig(self, enabled: bool, trackStats: bool, heatmapType: int):
        self._enabled = enabled

        if not self._enabled:  # Flush remaining data in case we disable monitor
            self.flushMonitorData()
            self._sendMonitorData()

        if self._pipelineAnalyzer is not None:
            self._pipelineAnalyzer.changeConfig(trackStats, self.getPipeline())

        self._heatmap.changeType(heatmapType)

    def isTrackingStats(self):
        return self._pipelineAnalyzer is not None and self._pipelineAnalyzer.isTracking()

    def _shouldSendMonitorData(self) -> bool:
        return self.isPipelineRunning() and self._enabled

    def _threadFunction(self):
        MONITORING_UPDATE_INTERVAL = StreamVizzard.getConfig().MONITORING_UPDATE_INTERVAL

        while self._executeThread:
            time.sleep(MONITORING_UPDATE_INTERVAL)

            if self._shouldSendMonitorData():
                self._sendMonitorData()

    def _sendMonitorData(self):
        if not self.isPipelineRunning():
            return

        # TODO: BATCH MESSAGES TOGETHER?

        # SEND UPDATED OPERATORS

        with self._updatedOperatorLock:
            for operator in self._updatedOperators:
                if operator.getMonitor().isDataEnabled():
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

        # SEND UPDATED BROKER

        with self._updateMessageBrokerLock:
            if len(self._messageBrokerUpdates) > 0:
                if self._messageBrokerTuple is None:
                    self._messageBrokerTuple = MessageBrokerSocketTuple(self._onMessageBrokerTupleSend, list(self._messageBrokerUpdates.keys()))
                    self.serverManager.sendSocketData(self._messageBrokerTuple)
                else:
                    self._messageBrokerTuple.operators = list(self._messageBrokerUpdates.keys())

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
        if self._messageBrokerTuple is None:
            return

        with self._updateMessageBrokerLock:
            self._messageBrokerUpdates.clear()
            self._messageBrokerTuple = None

    def _onHMTupleSend(self, st: SocketTuple):
        self._heatmapSendState = None
