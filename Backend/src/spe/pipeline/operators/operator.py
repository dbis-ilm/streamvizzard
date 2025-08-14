from __future__ import annotations
import asyncio
import logging
import sys
import traceback
import uuid
from asyncio import Future
from collections import deque
from enum import Enum
from typing import Optional, List, Deque, Dict, TYPE_CHECKING, Type, Set

from spe.pipeline.socket import Socket
from abc import ABC, abstractmethod

from spe.runtime.compiler.definitions.compileOpFunction import InferExecutionCodeCOF
from spe.runtime.compiler.definitions.compileOpMetaData import CompileOpMetaData
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.runtime.debugger.debugMethods import debugMethod
from spe.runtime.debugger.debugStep import DebugStepType, StepContinuation
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.debugger.history.historyState import HistoryState
from spe.common.iEventEmitter import IEventEmitter
from spe.common.timer import Timer
from spe.common.tuple import Tuple
from streamVizzard import StreamVizzard
from utils.messages import Messages

if TYPE_CHECKING:
    from spe.pipeline.connection import Connection


class OperatorType(Enum):
    DEFAULT = 1
    SOURCE = 2
    SINK = 3


class Operator(ABC, IEventEmitter):
    """
    An operator receives one input tuple and may produce one output tuple
    The data element of the Tuple contains an entry for each ingoing or outgoing socket
    The values of those entries might be None:
    (None, 1, None) -> (2, 4)
    """

    EVENT_TUPLE_PROCESSED = "onTupleProcessed"  # [processedTuple, exTime] After the tuple has been processed. Attributes: Tuple Out, ExTime
    EVENT_TUPLE_PRE_PROCESSED = "preTupleProcessed"  # [processedTuple] Before the tuple will be processed. Attributes: Tuple In

    def __init__(self, opID: int, socketsIn: int, socketsOut: int,
                 staticDataObject: bool = False, supportsDebugging: bool = True):
        super(Operator, self).__init__()

        self.id = opID  # Unique ID reflecting the operator entity in the pipeline
        self.uuid = uuid.uuid4().hex  # Unique ID reflecting current data parameter configurations
        self.inputs: List[Socket] = list()
        self.outputs: List[Socket] = list()

        self._eventLoop: Optional[asyncio.AbstractEventLoop] = None
        self._messageBroker = Operator.MessageBroker(self)

        self.staticDataObject = staticDataObject  # If no deep copy of the object should occur in transmit
        self._supportDebugging = supportsDebugging  # If this operator does support debugging

        self._runtimeCreated = False

        self._currentError: Optional[str] = None

        # Setup utils

        self._monitor = None
        self._debugger = None
        self._advisor = None

        if StreamVizzard.getConfig().MONITORING_ENABLED:
            from spe.runtime.monitor.operatorMonitor import OperatorMonitor
            self._monitor = OperatorMonitor(self)

        if StreamVizzard.getConfig().ADVISOR_ENABLED:
            from spe.runtime.advisor.operatorAdvisor import OperatorAdvisor
            self._advisor = OperatorAdvisor(self)

        if StreamVizzard.getConfig().DEBUGGER_ENABLED:
            from spe.runtime.debugger.operatorDebugger import OperatorDebugger
            self._debugger = OperatorDebugger(self)

        # Determine operator type

        from spe.pipeline.operators.source import Source
        from spe.pipeline.operators.sink import Sink

        if isinstance(self, Source):
            self._operatorType = OperatorType.SOURCE
        elif isinstance(self, Sink):
            self._operatorType = OperatorType.SINK
        else:
            self._operatorType = OperatorType.DEFAULT

        self._configureSockets(socketsIn, socketsOut)

    @property
    def allowedParents(self) -> Optional[List[Type[Operator]]]:
        return None

    @property
    def allowedChildren(self) -> Optional[List[Type[Operator]]]:
        return None

    def _configureSockets(self, socketsIn: int, socketsOut: int):
        socketsChanged = socketsIn != len(self.inputs) or socketsOut != len(self.outputs)

        if not socketsChanged:
            return

        oldIns = self.inputs.copy()
        oldOuts = self.outputs.copy()

        self.inputs.clear()
        self.outputs.clear()

        if socketsIn > 0:
            for i in range(0, socketsIn):
                if i < len(oldIns):
                    self.inputs.append(oldIns[i])
                else:
                    self.inputs.append(Socket(self, len(self.inputs), True))

        if socketsOut > 0:
            for i in range(0, socketsOut):
                if i < len(oldOuts):
                    self.outputs.append(oldOuts[i])
                else:
                    self.outputs.append(Socket(self, len(self.outputs), False))

        self._messageBroker.setupMessageQueues()

    def onExecutionError(self, error: Optional[str] = None, showErrorLine: bool = False):
        T, V, TB = sys.exc_info()

        # Extract error msg from exception if error txt is not set
        if error is None:
            tb = traceback.extract_tb(TB)
            res = traceback.format_exception_only(T, V)

            error = res[len(res) - 1] + "\n".join(res[:len(res) - 1])

            if showErrorLine:
                error = "[Line " + str(tb[-1].lineno) + "] " + error

        self._currentError = error

        # Send error
        if self._monitor is not None:
            self._monitor.notifyError(error)

        # Print exception
        if T is not None:
            logging.log(logging.ERROR, traceback.format_exc())

    def clearExecutionError(self):
        self._updateError(None)

    def _updateError(self, error: Optional[str]):
        if error is None and self._currentError is not None:
            if (monitor := self.getMonitor()) is not None:
                monitor.notifyError(None)  # Notify cleared error

            self._currentError = None
        elif error is not None:
            self.onExecutionError(error)

    def exportOperatorData(self) -> dict:
        from spe.pipeline.operators.operatorDB import getPathByOperator

        def getID(operator: Operator):
            return {"id": operator.id, "path": getPathByOperator(type(operator)), "uuid": operator.uuid}

        # Inputs / Outputs

        inputs = []
        outputs = []

        for sock in self.inputs:
            connected = []

            for con in sock.getConnections():
                connected.append({"socket": con.output.id, "component": getID(con.output.op), "id": con.id})

            inputs.append({"socket": sock.id, "connected": connected})

        for sock in self.outputs:
            connected = []

            for con in sock.getConnections():
                connected.append({"socket": con.input.id, "component": getID(con.input.op), "id": con.id})

            outputs.append({"socket": sock.id, "connected": connected})

        return {"id": getID(self),
                "inputs": inputs,
                "outputs": outputs,
                "data": self.getData(),
                "monitor": self.getMonitor().getCtrlData() if self.getMonitor() is not None else None,
                "breakpoints": self.getDebugger().exportBreakpoints() if self.getDebugger() is not None else None}

    def setMonitorData(self, monitorData):
        if self.getMonitor() is not None and monitorData is not None:
            self.getMonitor().setCtrlData(monitorData)

    def setBreakpointData(self, breakpointData):
        if self.getDebugger() is not None and breakpointData is not None:
            self.getDebugger().registerBreakpoints(breakpointData)

    # --------------------------- GETTER ----------------------------

    def isSource(self):
        return self._operatorType == OperatorType.SOURCE

    def isSink(self):
        return self._operatorType == OperatorType.SINK

    def getName(self) -> str:
        return self.__class__.__name__

    def getUniqueName(self) -> str:
        return self.getName() + "_" + str(self.id)

    def getInput(self, socketID) -> Optional[Socket]:
        if socketID >= len(self.inputs):
            return None

        return self.inputs[socketID]

    def getOutput(self, socketID) -> Optional[Socket]:
        if socketID >= len(self.outputs):
            return None

        return self.outputs[socketID]

    def getNeighbours(self, includeInputs: bool = True, includeOutputs: bool = True) -> List[Operator]:
        # Map from connections to (other) ops
        cons = self.getConnections(includeInputs, includeOutputs)

        n: List[Operator] = list()

        for c in cons:
            n.append(c.input.op if c.input.op != self else c.output.op)

        return n

    def getGlobalNeighbours(self, includeInputs: bool = True, includeOutputs: bool = True) -> List[Operator]:
        """ Returns all IN or OUT neighbours of this operator, globally, not only direct neighbours. """

        ops: List[Operator] = list()

        if includeInputs:
            visited: Set[int] = set()
            inNQueue = self.getNeighbours(True, False)

            while inNQueue:
                n = inNQueue.pop(0)

                if n.id in visited:
                    continue

                visited.add(n.id)
                ops.append(n)

                inNQueue.extend(n.getNeighbours(True, False))

        if includeOutputs:
            visited: Set[int] = set()
            outNQueue = self.getNeighbours(False, True)

            while outNQueue:
                n = outNQueue.pop(0)

                if n.id in visited:
                    continue

                visited.add(n.id)
                ops.append(n)

                outNQueue.extend(n.getNeighbours(False, True))

        return ops

    def getConnections(self, includeIns: bool = True, includeOuts: bool = True) -> List[Connection]:
        n: List[Connection] = list()

        # Operator inputs

        if includeIns:
            for inSock in self.inputs:
                for con in inSock.getConnections():
                    n.append(con)

        # Operator outputs

        if includeOuts:
            for outSock in self.outputs:
                for con in outSock.getConnections():
                    n.append(con)

        return n

    def hasOutConnections(self) -> bool:
        for out in self.outputs:
            if out.hasConnections():
                return True

        return False

    def getMonitor(self):
        return self._monitor

    def getDebugger(self):
        return self._debugger

    def isRunning(self) -> bool:
        return self._runtimeCreated

    def getEventLoop(self):
        return self._eventLoop

    def getBroker(self):
        return self._messageBroker

    # ---------------------------- COMPILER ----------------------------

    def deriveOutThroughput(self, inTp: float):
        """ Determines the maximum out throughput that can be achieved by this operator based on the inTp.
        Operators, such as windows might return values different from the inTp due to collecting values. """

        return inTp  # Regular operators have an 1:1 processing of data

    def getCompileMetaData(self) -> CompileOpMetaData:
        return CompileOpMetaData()

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        if InferExecutionCodeCOF.canAutoInfer(self):
            return [CompileOpSpecs.getDefaultInferable()]
        else:
            return [CompileOpSpecs.getSVDefault()]

    # -------------------------- PIPE DEBUGGER -------------------------

    def continueExecution(self):
        self.getBroker().continueExecution()

    def isDebuggingEnabled(self, checkSupported: bool = True):
        en = self._debugger is not None and self._debugger.getDebugger().isEnabled()

        return en if not checkSupported else en and checkSupported and self.isDebuggingSupported()

    def getHistoryState(self) -> Optional[HistoryState]:
        if self.isDebuggingEnabled(False):
            return self._debugger.getDebugger().getHistoryState()

        return None

    def isDebuggingSupported(self):
        return self._supportDebugging

    # ---

    async def _debugProcessTuple(self, _tuple: Tuple):
        return await self._debugger.registerStep(DebugStepType.PRE_TUPLE_PROCESSED,
                                                 self._debugger.getDT(_tuple),
                                                 undo=lambda tup: self._eventListener.execute(self.EVENT_TUPLE_PRE_PROCESSED, [tup]),
                                                 redo=lambda tup: self._eventListener.execute(self.EVENT_TUPLE_PRE_PROCESSED, [tup]),
                                                 cont=StepContinuation(DebugStepType.ON_OP_EXECUTED, self._onOperatorExecute))

    async def _debugExecuteOperator(self, _tuple: Tuple):
        resTuple = self.createTuple(())  # Required to have access to result tuple

        return await self._debugger.registerStep(DebugStepType.ON_OP_EXECUTED,
                                                 DebugTuple(self._debugger, resTuple),
                                                 undo=lambda tup: self._undoRedoExecute(True, tup),
                                                 redo=lambda tup: self._undoRedoExecute(False, tup),
                                                 cont=StepContinuation(DebugStepType.ON_TUPLE_PROCESSED,
                                                                       self._contExecute, self._canContExecute))

    def _canContExecute(self, rT: Tuple) -> bool:
        if not rT.isValidTuple():  # Error or Dropped
            return False

        exTime = self._debugger.getDT(rT).getAttribute("exTime")

        return exTime is not None  # None=onTupleProcessed was never called with this tuple (ex returned None)

    async def _contExecute(self, rT: Tuple):
        exTime = self._debugger.getDT(rT).getAttribute("exTime")

        await self._onTupleProcessed(rT, exTime)

    def _undoRedoExecute(self, undo: bool, tup: Tuple):
        dt = self.getDebugger().getDT(tup)

        # Errors occurring during setData are handled by pipelineUpdates
        err = dt.getAttribute("opExError")

        if undo:
            self._onExecutionUndo(tup)
            self._updateError(err["prev"] if err is not None else None)
        else:
            self._onExecutionRedo(tup)
            self._updateError(err["current"] if err is not None else None)

    def _onExecutionUndo(self, tup: Tuple):
        ...  # May be implemented by children to add custom logic

    def _onExecutionRedo(self, tup: Tuple):
        ...  # May be implemented by children to add custom logic

    def _getExecuteDT(self):
        return self.getDebugger().getLastDTForStep(DebugStepType.ON_OP_EXECUTED)

    async def _debugOnTupleProcessed(self, tupleIn: Tuple, executionTime: float):
        dt = self.getDebugger().getDT(tupleIn)
        dt.registerAttribute("exTime", executionTime)

        # Execution time will be accessed as dt attribute in operatorMonitor
        return await self._debugger.registerStep(DebugStepType.ON_TUPLE_PROCESSED, dt,
                                                 undo=lambda tup: self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [tup, 0]),
                                                 redo=lambda tup: self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [tup, 0]),
                                                 cont=StepContinuation(DebugStepType.ON_TUPLE_TRANSMITTED, self._distributeTuple, self._canContProcessed))

    def _canContProcessed(self, tupleIn: Tuple) -> bool:
        return self.hasOutConnections() and not tupleIn.isSinkTuple()

    def _undoRedoDistribute(self, undo: bool, tup: Tuple):
        for socketID in range(0, len(self.outputs)):
            socket = self.outputs[socketID]

            if len(socket.getConnections()) == 0:
                continue

            for connection in socket.getConnections():
                targetOp: Operator = connection.input.op

                connection.onTupleTransmitted(tup)

                resTuple = self.createTuple((tup.data[socketID],))
                resTuple.socketID = connection.input.id

                if undo:
                    targetOp._undoSendTuple(resTuple)
                else:
                    targetOp.sendTuple(resTuple)

    async def _debugDistribute(self, tupleIn: Tuple):
        # Check if there are any connections to send to before storing a step

        if not self.hasOutConnections():
            return None

        # For both redo/undo actions the nextDT is required since there are all required data elements stored to redo/undo
        return await self._debugger.registerStep(DebugStepType.ON_TUPLE_TRANSMITTED, self._debugger.getDT(tupleIn),
                                                 undo=lambda tup: self._undoRedoDistribute(True, tup),
                                                 redo=lambda tup: self._undoRedoDistribute(False, tup),
                                                 cont=None)

    # ----------------------------------------------------------------

    def createTuple(self, data: tuple) -> Tuple:
        return Tuple(data, self)

    def createSinkTuple(self) -> Tuple:
        return Tuple.createSinkTuple(self)

    def createErrorTuple(self, error: Optional[str] = None) -> Tuple:
        self.onExecutionError(error)

        return Tuple.createErrorTuple(self)

    def createDroppedTuple(self):
        return Tuple.createDroppedTuple(self)

    def onRuntimeCreate(self, eventLoop: asyncio.AbstractEventLoop):
        self._runtimeCreated = True

        self._eventLoop = eventLoop

        self._messageBroker.createRuntime(eventLoop)

    def onRuntimeDestroy(self):
        self._runtimeCreated = False

        self._messageBroker.destroyRuntime(self._eventLoop)

        self._eventLoop = None

    # ---------------------------- PROCESS ---------------------------

    @debugMethod(_debugProcessTuple)
    async def _processTuple(self, _tuple: Tuple):
        self._eventListener.execute(self.EVENT_TUPLE_PRE_PROCESSED, [_tuple])

        await self._onOperatorExecute(_tuple)

    @debugMethod(_debugExecuteOperator)
    async def _onOperatorExecute(self, tupleIn: Tuple):
        # Stopped
        if not self.isRunning():
            return

        if not self.staticDataObject:
            # Creates a copy of the input data to not impact previous DTs or parallel executions
            # Premise: The internal tuple data will never change before or after this execute call
            tupleIn = tupleIn.clone(True)

            if not self.isRunning():
                return

        prevError = self._currentError

        try:
            # Execute real operator task in parallel
            # Care: For CPU heavy tasks a ProcessPoolExecutor would be more suitable
            # However, data share / copy needs to be handled in this case
            # None uses the asyncio default ThreadPoolExecutor (which shares GLI)

            # Awaiting the result introduces additional overhead that might be higher than short running execute funcs.
            # However, this overhead is usually in sub-millisecond range (~0.4ms) and can be neglected.
            # If system is on load, this overhead might be higher.
            # For this reason we track the pure execution time (which also may be affected by GLI slow-downs).

            if self._monitor is not None and self._monitor.getMonitor().isTrackingStats():
                tupleNew, elapsed = self._performExecute(tupleIn)  # Analytical mode | Reduces GLI overhead
            else:
                tupleNew, elapsed = await self._eventLoop.run_in_executor(None, self._performExecute, tupleIn)

            if tupleNew is None:
                tupleNew = self.createDroppedTuple()

            if self.isDebuggingEnabled():
                # Adjust already created result tuple, required to access new data in continuation
                # For long-running operators, it is important to pin to DT to not reload it from DISK
                # Care: Continuation might cancel task before long-running op has been completed, which is ok
                dt = self._getExecuteDT()

                if dt is None:
                    self.onExecutionError(Messages.DEBUGGER_DT_NOT_AVAILABLE.value)

                    return

                dt.setTupleData(tupleNew.data, True)

                if tupleNew.isErrorTuple():
                    errData = {"prev": prevError,
                               "current": self._currentError}
                    dt.registerAttribute("opExError", errData)

                dtTuple = dt.getTuple()
                dtTuple.state = tupleNew.state
                tupleNew = dtTuple

            if not tupleNew.isValidTuple():  # None/Error values are dropped
                return

            self.clearExecutionError()

            await self._onTupleProcessed(tupleNew, elapsed)
        except Exception:
            self.onExecutionError()

    def _performExecute(self, inputData: Tuple) -> tuple[Optional[Tuple], float]:
        start = Timer.currentRealTime()

        outputData = self._execute(inputData)

        end = Timer.currentRealTime()

        return outputData, end - start

    @debugMethod(_debugOnTupleProcessed)
    async def _onTupleProcessed(self, tupleIn: Tuple, executionTime: float):
        self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [tupleIn, executionTime])

        if tupleIn.isSinkTuple():
            return

        await self._distributeTuple(tupleIn)

    @debugMethod(_debugDistribute)
    async def _distributeTuple(self, tupleIn: Tuple):
        # Atomic function which pushes all tuples to following operators (main thread)

        _tuple = tupleIn.data

        if _tuple is None:
            return

        for socketID in range(0, len(self.outputs)):
            socket = self.outputs[socketID]

            conCount = len(socket.getConnections())

            if conCount == 0:
                continue

            for connection in socket.getConnections():
                targetOp = connection.input.op

                # Take part of tuple that belongs to this socket
                resTuple = self.createTuple((_tuple[socketID],))
                resTuple.socketID = connection.input.id

                connection.onTupleTransmitted(tupleIn)

                targetOp.sendTuple(resTuple)

    # ----------------------------------------------------------------

    @abstractmethod
    def setData(self, data: Dict):
        # Shouldn't do runtime-specific operations, such as opening files, ... -> use onRuntimeCreate
        # CARE: All parameters need to be present in the dictionary, also optional values!
        ...

    @abstractmethod
    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        ...

    @abstractmethod
    def getData(self) -> dict:
        ...

    # -------------------------- COMMUNICATION ------------------------

    def sendTuple(self, _tuple: Tuple):
        if not self.isRunning():
            return

        self._messageBroker.receiveTuple(_tuple)

    def _undoSendTuple(self, prevTuple: Tuple):
        if not self.isRunning() or not self.isDebuggingSupported():
            return

        self._messageBroker.undoReceiveTuple(prevTuple)

    class MessageBroker:
        """
        Broker of an operator that handles all communication and its own message queue
        """

        def __init__(self, operator):
            self._operator: Operator = operator

            self._queueEvent: Optional[asyncio.Event] = None

            # Each socket of the operator will have its own message queue
            self._messageQueue: List[Deque] = []
            self._totalMessages = 0

            self._futureThread: Optional[Future] = None

        def setupMessageQueues(self):
            oldL = len(self._messageQueue)
            newL = len(self._operator.inputs)

            # Create message queues for each input socket, take existing queues if possible
            # This allows to recover old data when socket count changes
            # Assumption: Data in queues is never lost and must be processed to be cleared
            for sID in range(max(oldL, newL)):
                if sID >= oldL:
                    self._messageQueue.append(deque())

            # Update total message count

            self._totalMessages = 0

            for qID in range(len(self._operator.inputs)):
                self._totalMessages += len(self._messageQueue[qID])

            if self._queueEvent is not None and self._totalMessages == 0:
                self._queueEvent.clear()

        def receiveTuple(self, _tuple: Tuple):
            if not self._operator.isRunning():
                return

            self._messageQueue[_tuple.socketID].append(_tuple.data[0])

            self._totalMessages += 1

            self._queueEvent.set()

            self._notifyMessageQueueChanged()

        # -------------------------------- DEBUGGER --------------------------------

        def continueExecution(self):
            # Cancels current process task and starts a new one to purge outdated operations

            self._futureThread.cancel()

            self._futureThread = asyncio.ensure_future(self._processLoop(), loop=self._operator.getEventLoop())

        def getMessageCount(self):
            return [len(q) for q in self._messageQueue]

        def undoReceiveTuple(self, t: Tuple):
            self._messageQueue[t.socketID].pop()

            self._totalMessages -= 1

            if self._totalMessages == 0:
                self._queueEvent.clear()

            self._notifyMessageQueueChanged()

        async def _debugProcessTuple(self, resTuple: Tuple):
            return await self._operator.getDebugger().registerStep(DebugStepType.ON_STREAM_PROCESS_TUPLE,
                                                                   DebugTuple(self._operator.getDebugger(), resTuple),
                                                                   undo=lambda tup: self._undoProcessElement(tup),
                                                                   redo=lambda tup: self._createMessageTuple(),
                                                                   cont=StepContinuation(DebugStepType.PRE_TUPLE_PROCESSED, self._operator._processTuple))

        def _undoProcessElement(self, processedTuple: Tuple):
            for i in range(len(processedTuple.data)):
                data = processedTuple.data[i]

                # If we have real data
                if data is not None:
                    self._messageQueue[i].appendleft(processedTuple.data[i])

                    self._totalMessages += 1

            self._notifyMessageQueueChanged()

        # --------------------------------------------------------------------------

        async def _processLoop(self):
            try:
                while self._operator.isRunning():
                    if self._operator.isDebuggingEnabled():
                        # In case the history is paused, wait for continuation, since undo triggers queueEvent.
                        # If the loop is canceled during continuation wait before pipeline is resumed.

                        await self._operator.getDebugger().getDebugger().getHistoryEvent().wait()

                    self._queueEvent.clear()

                    while self._totalMessages > 0:
                        if not self._operator.isRunning():
                            return

                        # Check if it is possible to process a tuple

                        canProcessTuple = True
                        for qID in range(len(self._operator.inputs)):
                            q = self._messageQueue[qID]
                            if len(q) == 0:
                                canProcessTuple = False

                                break

                        if not canProcessTuple:
                            break

                        resTuple = self._operator.createTuple(())

                        await self._processTuple(resTuple)

                    if not self._operator.isRunning():  # Closed
                        return

                    await self._queueEvent.wait()

            except Exception:
                logging.log(logging.ERROR, traceback.format_exc())

        @debugMethod(_debugProcessTuple)
        async def _processTuple(self, resTuple: Tuple):
            if not self._operator.isRunning():
                return

            # Fill tuple with elements
            resTuple.data = self._createMessageTuple()

            if self._operator.isDebuggingEnabled():
                self._operator.getDebugger().getDT(resTuple).setTupleData(resTuple.data, True)

            await self._operator._processTuple(resTuple)

        def _createMessageTuple(self) -> tuple:
            messageElements = []

            for qID in range(len(self._operator.inputs)):
                q = self._messageQueue[qID]

                if len(q) > 0:
                    messageElements.append(q.popleft())

                    self._totalMessages -= 1
                else:
                    raise Exception("No elements in message queue for op " + str(self._operator.id) + " and socket " + str(qID) + "!")

            self._notifyMessageQueueChanged()

            return tuple(messageElements)

        def _notifyMessageQueueChanged(self):
            if self._operator.getMonitor() is not None:
                self._operator.getMonitor().getMonitor().onOpMessageQueueChanged(self._operator)

        # --------------------------------------------------------------------------

        def createRuntime(self, eventLoop: asyncio.AbstractEventLoop):
            self._queueEvent = asyncio.Event()

            self._futureThread = asyncio.ensure_future(self._processLoop(), loop=eventLoop)

        def destroyRuntime(self, eventLoop: asyncio.AbstractEventLoop):
            if eventLoop.is_running() and self._futureThread is not None:
                self._futureThread.cancel()

            self._futureThread = None

            self._queueEvent = None
