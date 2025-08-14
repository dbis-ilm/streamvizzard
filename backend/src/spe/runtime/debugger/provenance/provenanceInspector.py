from __future__ import annotations

import json
import logging
import threading
import traceback
from collections import deque
from typing import TYPE_CHECKING, List, Optional, Dict, Deque

from provinspector.data import PipelineChangeData, DebugStepData, ConnectionCreationPipelineChangeData, \
    OperatorCreationPipelineChangeData, OperatorDeletionPipelineChangeData, OperatorModificationPipelineChangeData, \
    ConnectionDeletionPipelineChangeData
from provinspector.domain.constants import OperatorStepType
from provinspector.domain.model import Metric
from provinspector.provinspector import ProvInspector
from provinspector.storage.adapter import Neo4JAdapter
from provinspector.storage.database import ProvGraphDatabase
from provinspector.utils.dumper import JsonDumper

from spe.runtime.debugger.provenance.provQueryParser import ProvQueryParser
from spe.common.timer import Timer
from streamVizzard import StreamVizzard
from spe.pipeline.pipelineUpdates import OperatorAddedPU, OperatorRemovedPU, OperatorDataUpdatedPU, \
    ConnectionAddedPU, ConnectionRemovedPU, PipelineUpdate
from spe.runtime.debugger.debugStep import DebugStepType

if TYPE_CHECKING:
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger
    from spe.runtime.debugger.debugStep import DebugStep


# TODO: Purge database when steps are evicted from buffer manager?

class ProvenanceInspector:
    class StepRegEntry:
        def __init__(self, step: DebugStep):
            self.step = step
            self.ready = False

            self.regTime = Timer.currentRealTime()
            self.stepGraphData: Optional[DebugStepData] = None

    def __init__(self, debugger: PipelineDebugger):
        self._debugger = debugger

        StreamVizzard.registerShutdownHook(self.destroy)

        try:
            self._inspector = ProvInspector(provenance_database=ProvGraphDatabase(
                    adapter=Neo4JAdapter(
                        docker_socket=StreamVizzard.getConfig().DEBUGGER_PROV_DOCKER_SOCKET,
                    )
                ))  # Executed on system start
        except Exception:
            print("Failed to start Neo4J database!")

            logging.log(logging.ERROR, traceback.format_exc())

            return

        self._enabled = False
        self._running = False

        self._updateThread: Optional[threading.Thread] = None
        self._updateEvent: Optional[threading.Event] = None
        self._updateQueue: Deque[DebugStepData] = deque()

        self._registerQueue: Deque[ProvenanceInspector.StepRegEntry] = deque()
        self._registerThread: Optional[threading.Thread] = None
        self._registerEvent: Optional[threading.Event] = None
        self._registerLastStepLookup: Dict[int, ProvenanceInspector.StepRegEntry] = dict()
        self._stepReadyEvent: Optional[threading.Event] = None

        self._updatesCompletedEvent: Optional[threading.Event] = None
        self._completeUpdatesBeforeQuery = True
        self._queryThread: Optional[threading.Thread] = None

        self._opMetricChangeTracker: Dict[str, float] = dict()  # OpID#ParmName,Val
        self._lastBranchID = 0

        self._createDataDump = False
        self._executeData = []
        self._initData = []

    def initialize(self):
        if self._enabled:
            self._initializeGraph()

    def shutdown(self):
        if self._createDataDump and len(self._executeData) > 0:
            with open('C:/Users/timor/Documents/Paper/Eigene/ICDE2024/Messung/v2/DebuggerPerformance/historyDump_ex.txt', 'w') as f:
                for e in self._executeData:
                    f.write(e + "\n")

            with open('C:/Users/timor/Documents/Paper/Eigene/ICDE2024/Messung/v2/DebuggerPerformance/historyDump_ini.txt', 'w') as f:
                for e in self._initData:
                    f.write(e + "\n")

            self._executeData.clear()
            self._initData.clear()

        self._running = False

    def reset(self):
        self._running = False

        self._opMetricChangeTracker.clear()
        self._lastBranchID = 0

        if self._inspector is not None:
            try:
                self._inspector.clear()
            except Exception:
                pass

        if self._updateEvent is not None:
            self._updateEvent.set()  # Gracefully release waits

        if self._updatesCompletedEvent is not None:
            self._updatesCompletedEvent.set()

        if self._registerEvent is not None:
            self._registerEvent.set()

        if self._stepReadyEvent is not None:
            self._stepReadyEvent.set()

        self._registerQueue.clear()
        self._registerThread = None
        self._registerEvent = None
        self._stepReadyEvent = None
        self._registerLastStepLookup.clear()

        self._updateEvent = None
        self._updateThread = None
        self._updateQueue.clear()
        self._updatesCompletedEvent = None
        self._queryThread = None

    def destroy(self):
        if self._inspector is not None:
            self._inspector.shutdown()
            self._inspector = None

    def enable(self):
        if self._enabled:
            return

        self._initializeGraph()

        self._enabled = True

    def disable(self):
        if not self._enabled:
            return

        self._enabled = False

        self.reset()

    def changeConfig(self, awaitUpdates: bool):
        self._completeUpdatesBeforeQuery = awaitUpdates

        if not awaitUpdates and self._updatesCompletedEvent is not None:
            self._updatesCompletedEvent.set()  # Release event to trigger query if waiting

    def onDebugStepRegistered(self, ds: DebugStep):
        if not self._isAccessible():
            return

        # Get previous ds of this operator and extract their data since that step is
        # now completed when we register a new step of that operator

        prev = self._registerLastStepLookup.get(ds.debugger.getOperator().id, None)

        if prev is not None and not prev.ready:
            prev.stepGraphData = self._extractDebugStepGraphData(prev.step)
            prev.ready = True

            if prev == self._registerQueue[0]:
                self._stepReadyEvent.set()

        newEntry = ProvenanceInspector.StepRegEntry(ds)

        self._registerLastStepLookup[ds.debugger.getOperator().id] = newEntry
        self._registerQueue.append(newEntry)

        self._registerEvent.set()

    def queryFromTemplate(self, inputData):
        if not self._isAccessible():
            return None

        if self._queryThread is not None:
            return  # Last query still running

        self._queryThread = threading.Thread(target=self._queryThreadFunc, args=(inputData,))
        self._queryThread.start()

    def queryProvenance(self, query: str):
        if not self._isAccessible():
            return None

        if self._completeUpdatesBeforeQuery:  # Blocking call
            self._updatesCompletedEvent.wait()

        if not self._isAccessible():
            return None

        try:
            return self._inspector.query(query)
        except Exception:
            if self._running:
                print("Failed to execute query!")

                logging.log(logging.ERROR, traceback.format_exc())

            return None

    def _queryThreadFunc(self, inputData) -> Optional[Dict]:
        def returnError():
            self._debugger.getServerManager().sendSocketData(json.dumps({"cmd": "provQueryRes", "data": None}))

        queryTemplate = ProvQueryParser.createQueryTemplate(inputData)

        if queryTemplate is None:
            returnError()
            return

        res = self.queryProvenance(queryTemplate.generateQuery())

        if res is None:
            returnError()
            return

        extractedResult = queryTemplate.extractResult(self, res)

        self._debugger.getServerManager().sendSocketData(json.dumps({"cmd": "provQueryRes", "data": extractedResult}))

        self._queryThread = None

        return extractedResult

    def _isAccessible(self) -> bool:
        return self._enabled and self._inspector is not None and self._running

    def _registerThreadFunc(self):
        while self._running:
            self._registerEvent.wait()

            while self._registerQueue:
                # Metrics of the step might not be ready yet (write-ahead-logging), so wait until this
                # step is ready (when the next step of that operator is processed or timeout reached)
                # Timeout will be reached, e.g. when there is no next step or op execution takes a long time

                if not self._registerQueue[0].ready:
                    self._stepReadyEvent.wait(0.25)

                self._stepReadyEvent.clear()

                if not self._isAccessible():
                    return

                entry = self._registerQueue.popleft()

                # In case entry is not ready yet (timeout reached), we extract the data immediately, otherwise it already was extracted

                if not entry.ready:
                    entry.stepGraphData = self._extractDebugStepGraphData(entry.step)
                    entry.ready = True

                    # Also set all other steps to ready that exceeded the timeout

                    readyTargetTime = Timer.currentRealTime()

                    for step in self._registerQueue:
                        if not step.ready and step.regTime + 0.25 >= readyTargetTime:
                            step.stepGraphData = self._extractDebugStepGraphData(step.step)
                            step.ready = True

                if entry.stepGraphData is None:
                    continue

                self._updateQueue.append(entry.stepGraphData)

                self._updatesCompletedEvent.clear()
                self._updateEvent.set()

            if not self._isAccessible():
                return

            self._registerEvent.clear()

    def _updateThreadFunc(self):
        while self._running:
            self._updateEvent.wait()

            while self._updateQueue:
                stepData = self._updateQueue.popleft()

                if not self._isAccessible():
                    return

                self._updateGraph(stepData)

            if not self._isAccessible():
                return

            self._updateEvent.clear()
            self._updatesCompletedEvent.set()

    def _extractDebugStepGraphData(self, ds: DebugStep) -> Optional[DebugStepData]:
        parentBranch = self._debugger.getHistory().getBranch(ds.branchID).parentBranch
        op = ds.debugger.getOperator()

        opType = self._convertDSType(ds.type)

        metrics: Optional[List[Metric]] = None

        # Clear metric tracker in case of updates or if we split into a new branch to
        # populate the newly created pipeline revision with metric information

        if ds.hasUpdates() or ds.branchID != self._lastBranchID:
            self._opMetricChangeTracker.clear()

        self._lastBranchID = ds.branchID

        # Extract metric data based on debug step type
        # Only generate metrics if their data changed

        if ds.type == DebugStepType.ON_TUPLE_PROCESSED:
            exTime = self._createMetric(op.id, "avgExTime", op.getMonitor().getAvgExecutionTime(),
                                        True, StreamVizzard.getConfig().DEBUGGER_PROV_METRICS_EXTIME_THRESHOLD)

            if exTime is not None:
                metrics = [exTime]

            # Currently unused for queries
            # dataSize = self._createMetric(op.id, "avgDataSize", op.getMonitor().getAvgDataSize(), True, self._dataSizeRefVal)
            # if dataSize is not None:
            #     metrics.append(dataSize)

        elif ds.type == DebugStepType.ON_STREAM_PROCESS_TUPLE:
            metrics = []
            # Currently unused for queries
            # messageQueueState = op.getBroker().getMessageCount()
            #
            # for inID in range(len(op.inputs)):
            #     if inID < len(messageQueueState):
            #         ms = self._createMetric(op.id, "messageQueueSize_" + "_" + str(inID), messageQueueState[inID],
            #                                 False, config.DEBUGGER_PROV_METRICS_TUPCOUNT_THRESHOLD)
            #         if ms is not None:
            #             metrics.append(ms)
        elif ds.type == DebugStepType.ON_TUPLE_TRANSMITTED:
            metrics = []

            # Currently unused for queries
            # messageQueueState = op.getBroker().getMessageCount()
            #
            # for inID in range(len(op.inputs)):
            #     if inID < len(messageQueueState):
            #         ms = self._createMetric(op.id, "messageQueueSize_" + "_" + str(inID), messageQueueState[inID],
            #                                 False, config.DEBUGGER_PROV_METRICS_TUPCOUNT_THRESHOLD)
            #         if ms is not None:
            #             metrics.append(ms)

            for out in op.outputs:
                for con in out.getConnections():
                    tp = self._createMetric(op.id, "throughput_" + str(con.id), con.getMonitor().throughput,
                                            True, StreamVizzard.getConfig().DEBUGGER_PROV_METRICS_EXTIME_THRESHOLD)
                    if tp is not None:
                        metrics.append(tp)

                    # Currently unused for queries
                    # tt = self._createMetric(con.id, "totalTuples_" + str(con.id), con.getMonitor().totalTuples, False, self._tupleCountRefVal)
                    # if tt is not None:
                    #     metrics.append(tt)

        # Extract pipeline update data

        changes: Optional[List[PipelineChangeData]] = None

        if ds.hasUpdates():
            changes = []

            for pu in ds.pipelineUpdates:
                puChange = self._convertPipelineUpdate(ds.getUniqueID(), pu)

                if puChange is not None:
                    changes.append(puChange)

        if metrics is not None and len(metrics) == 0:
            metrics = None

        if metrics is None and changes is None:  # No need to register anything if nothing changed
            return None

        stepData = DebugStepData(ds.getUniqueID(), ds.time, ds.branchID, ds.localID,
                                 parentBranch.id if parentBranch is not None else None,
                                 op.id, op.__class__.__name__, opType, metrics, changes)

        if self._createDataDump:
            exD = JsonDumper.debug_step_data_to_json(stepData)
            self._executeData.append(exD)

        return stepData

    def _updateGraph(self, stepData: DebugStepData):
        if not self._isAccessible():
            return

        try:
            self._inspector.update([stepData])
        except Exception:
            if self._running:  # When closing there might be some error messages we can supress
                print("Failed to update prov graph!")

                logging.log(logging.ERROR, traceback.format_exc())

    def _initializeGraph(self):
        if self._running:
            return

        pipeline = self._debugger.getRuntimeManager().getPipeline()

        creationEvents = []

        for op in pipeline.getAllOperators():
            event = OperatorCreationPipelineChangeData("INI" + str(len(creationEvents)), op.id, op.__class__.__name__, op.getData())

            creationEvents.append(event)

            if self._createDataDump:
                self._initData.append(JsonDumper.pipeline_change_data_to_json(JsonDumper.pipeline_change_data_to_dict(event)))

        for con in pipeline.getAllConnections():
            event = ConnectionCreationPipelineChangeData("INI" + str(len(creationEvents)), con.id, con.output.op.id, con.input.op.id, con.output.id, con.input.id)

            creationEvents.append(event)

            if self._createDataDump:
                self._initData.append(JsonDumper.pipeline_change_data_to_json(JsonDumper.pipeline_change_data_to_dict(event)))

        try:
            self._inspector.initialize(creationEvents)
        except Exception:
            if self._running:  # When closing there might be some error messages we can supress
                print("Failed to initialize prov graph!")

                logging.log(logging.ERROR, traceback.format_exc())

            return

        self._updatesCompletedEvent = threading.Event()

        self._running = True

        self._updateEvent = threading.Event()
        self._updateThread = threading.Thread(target=self._updateThreadFunc)
        self._updateThread.start()

        self._stepReadyEvent = threading.Event()
        self._registerEvent = threading.Event()
        self._registerThread = threading.Thread(target=self._registerThreadFunc)
        self._registerThread.start()

    def _convertPipelineUpdate(self, dsID: str, pu: PipelineUpdate) -> Optional[PipelineChangeData]:
        uniqueID = dsID + "%" + str(pu.updateID)

        if isinstance(pu, OperatorAddedPU):
            op = self._debugger.getRuntimeManager().getPipeline().getOperator(pu.opID)
            return OperatorCreationPipelineChangeData(uniqueID, pu.opID, op.__class__.__name__, pu.opData)
        elif isinstance(pu, OperatorRemovedPU):
            op = self._debugger.getRuntimeManager().getPipeline().getOperator(pu.opID)
            return OperatorDeletionPipelineChangeData(uniqueID, pu.opID, op.__class__.__name__)
        elif isinstance(pu, OperatorDataUpdatedPU):
            op = self._debugger.getRuntimeManager().getPipeline().getOperator(pu.opID)
            return OperatorModificationPipelineChangeData(uniqueID, pu.opID, op.__class__.__name__, pu.param, pu.opData[pu.param])
        elif isinstance(pu, ConnectionAddedPU):
            return ConnectionCreationPipelineChangeData(uniqueID, pu.conID, pu.outOpID, pu.inOpID, pu.outSocketID, pu.inSocketID)
        elif isinstance(pu, ConnectionRemovedPU):
            return ConnectionDeletionPipelineChangeData(uniqueID, pu.conID, 0, 0, 0, 0)

        return None

    def _createMetric(self, opID: int, metricName: str, metricValue: float, percThres: bool, threshold: float) -> Optional[Metric]:
        mID = str(opID) + "#" + metricName

        prev = self._opMetricChangeTracker.get(mID, None)

        if prev is None:
            self._opMetricChangeTracker[mID] = metricValue
            return Metric(metricName, metricValue)
        else:
            if prev == metricValue:
                return None

            if percThres and prev != 0 and abs((metricValue / prev) - 1) < threshold:
                return None
            elif not percThres and abs(metricValue - prev) < threshold:
                return None

            self._opMetricChangeTracker[mID] = metricValue

            return Metric(metricName, metricValue)

    @staticmethod
    def _convertDSType(dsType: DebugStepType) -> Optional[OperatorStepType]:
        if dsType == DebugStepType.ON_OP_EXECUTED:
            return OperatorStepType.ON_OP_EXECUTED
        elif dsType == DebugStepType.ON_TUPLE_PROCESSED:
            return OperatorStepType.ON_TUPLE_PROCESSED
        elif dsType == DebugStepType.ON_SOURCE_PRODUCED_TUPLE:
            return OperatorStepType.ON_SOURCE_PRODUCED_TUPLE
        elif dsType == DebugStepType.ON_STREAM_PROCESS_TUPLE:
            return OperatorStepType.ON_STREAM_PROCESS_TUPLE
        elif dsType == DebugStepType.ON_TUPLE_TRANSMITTED:
            return OperatorStepType.ON_TUPLE_TRANSMITTED
        elif dsType == DebugStepType.PRE_TUPLE_PROCESSED:
            return OperatorStepType.PRE_TUPLE_PROCESSED

        return None

    def getDebugger(self) -> PipelineDebugger:
        return self._debugger

    def hasPendingUpdates(self):
        return len(self._updateQueue) > 0 or len(self._registerQueue) > 0
