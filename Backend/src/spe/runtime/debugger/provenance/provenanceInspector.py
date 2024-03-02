from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional, Dict

from provinspector.data import PipelineChangeData, DebugStepData, ConnectionCreationPipelineChangeData, \
    OperatorCreationPipelineChangeData, OperatorDeletionPipelineChangeData, OperatorModificationPipelineChangeData, \
    ConnectionDeletionPipelineChangeData, MetricData
from provinspector.domain.constants import OperatorStepType
from provinspector.provinspector import ProvInspector
from provinspector.storage.adapter import Neo4JAdapter
from provinspector.storage.database import ProvGraphDatabase

import config
from streamVizzard import StreamVizzard
from spe.pipeline.pipelineUpdates import OperatorAddedPU, OperatorRemovedPU, OperatorDataUpdatedPU, \
    ConnectionAddedPU, ConnectionRemovedPU, PipelineUpdate
from spe.runtime.debugger.debugStep import DebugStepType

if TYPE_CHECKING:
    from spe.runtime.debugger.pipelineDebugger import PipelineDebugger
    from spe.runtime.debugger.debugStep import DebugStep


class ProvenanceInspector:
    def __init__(self, debugger: PipelineDebugger):
        self._debugger = debugger

        StreamVizzard.registerShutdownHook(self.destroy)

        self._inspector = ProvInspector(provenance_database=ProvGraphDatabase(
                adapter=Neo4JAdapter(
                    docker_socket=config.DEBUGGER_PROV_DOCKER_SOCKET,
                )
            ))  # Executed on system start

        self._enabled = True

        self._opMetricChangeTracker: Dict[str, float] = dict()  # OpID#ParmName,Val

    def initialize(self):
        if self._enabled:
            self._iniPipeline()

    def shutdown(self):
        if not self._enabled:
            return

    def reset(self):
        if not self._enabled:
            return

        self._opMetricChangeTracker.clear()

        if self._inspector is not None:
            self._inspector.clear()

    def destroy(self):
        if self._inspector is not None:
            self._inspector.shutdown()
            self._inspector = None

    def enable(self):
        self._iniPipeline()

    def disable(self):
        self.reset()

        self._enabled = False

    def onDebugStepRegistered(self, ds: DebugStep):
        if not self._enabled:
            return

        parentBranch = self._debugger.getHistory().getBranch(ds.branchID).parentBranch
        op = ds.debugger.getOperator()

        opType = self._convertDSType(ds.type)

        metrics: Optional[List[MetricData]] = None

        # Extract metric data based on debug step type
        # Only generate metrics if their data changed

        if ds.type == DebugStepType.ON_TUPLE_PROCESSED:
            exTime = self._createMetric(op.id, "avgExTime", op.getMonitor().getAvgExecutionTime(),
                                        True, config.DEBUGGER_PROV_METRICS_EXTIME_THRESHOLD)
            if exTime is not None:
                metrics = [exTime]

        elif ds.type == DebugStepType.ON_STREAM_PROCESS_TUPLE:
            metrics = []
            messageQueueState = op.getBroker().getMessageCount()

            for inID in range(len(op.inputs)):
                if inID < len(messageQueueState):
                    ms = self._createMetric(op.id, "messageQueueSize_" + "_" + str(inID), messageQueueState[inID],
                                            False, config.DEBUGGER_PROV_METRICS_TUPCOUNT_THRESHOLD)
                    if ms is not None:
                        metrics.append(ms)
        elif ds.type == DebugStepType.ON_TUPLE_TRANSMITTED:
            metrics = []
            messageQueueState = op.getBroker().getMessageCount()

            for inID in range(len(op.inputs)):
                if inID < len(messageQueueState):
                    ms = self._createMetric(op.id, "messageQueueSize_" + "_" + str(inID), messageQueueState[inID],
                                            False, config.DEBUGGER_PROV_METRICS_TUPCOUNT_THRESHOLD)
                    if ms is not None:
                        metrics.append(ms)

            for out in op.outputs:
                for con in out.getConnections():
                    tp = self._createMetric(op.id, "throughput_" + str(con.id), con.getMonitor().throughput,
                                            True, config.DEBUGGER_PROV_METRICS_EXTIME_THRESHOLD)
                    if tp is not None:
                        metrics.append(tp)

                    if op.id == 4:
                        for i in range(25):
                            metrics.append(MetricData("throughput_" + str(con.id), con.getMonitor().throughput * (1 + random.random() / 2)))  # Add up to 1,5x the value

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
            return

        stepData = DebugStepData(ds.getUniqueID(), ds.time, ds.branchID, ds.localID,
                                 parentBranch.id if parentBranch is not None else None,
                                 op.id, op.__class__.__name__, opType, metrics, changes)

        self._inspector.update(stepData)

    def queryProvenance(self, query: str):
        return self._inspector.query(query)

    def _iniPipeline(self):
        pipeline = self._debugger.getRuntimeManager().getPipeline()

        creationEvents = []

        for op in pipeline.getAllOperators():
            event = OperatorCreationPipelineChangeData("INI" + str(len(creationEvents)), op.id, op.__class__.__name__, op.getData())

            creationEvents.append(event)

        for con in pipeline.getAllConnections():
            event = ConnectionCreationPipelineChangeData("INI" + str(len(creationEvents)), con.id, con.output.op.id, con.input.op.id, con.output.id, con.input.id)

            creationEvents.append(event)

        self._inspector.initialize(creationEvents)

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

    def _createMetric(self, opID: int, metricName: str, metricValue: float, percThres: bool, threshold: float) -> Optional[MetricData]:
        mID = str(opID) + "#" + metricName

        prev = self._opMetricChangeTracker.get(mID, None)

        if prev is None:
            self._opMetricChangeTracker[mID] = metricValue
            return MetricData(metricName, metricValue)
        else:
            if prev == metricValue:
                return None

            if percThres and prev != 0 and abs((metricValue / prev) - 1) < threshold:
                return None
            elif not percThres and abs(metricValue - prev) < threshold:
                return None

            self._opMetricChangeTracker[mID] = metricValue

            return MetricData(metricName, metricValue)

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
