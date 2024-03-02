import asyncio
import json
import logging
import sys
import traceback
from asyncio import Future
from collections import deque
from enum import Enum
from typing import Optional, List, Deque

import config
from spe.pipeline.socket import Socket
from abc import ABC, abstractmethod

from spe.runtime.debugger.debugMethods import debugMethod
from spe.runtime.debugger.debugStep import DebugStepType, DebugStep
from spe.runtime.debugger.debugTuple import DebugTuple
from spe.runtime.debugger.history.historyState import HistoryState
from spe.runtime.runtimeCommunicator import isDebuggerEnabled, onOpMessageQueueChanged, getHistoryState
from spe.runtime.structures.iEventEmitter import IEventEmitter
from spe.runtime.structures.timer import Timer
from spe.runtime.structures.tuple import Tuple


class OperatorType(Enum):
    DEFAULT = 1
    SOURCE = 2


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
                 allowNoneMerge: bool = False, pipelineBreaker: bool = False,
                 staticDataObject: bool = False, supportsDebugging: bool = True):
        super(Operator, self).__init__()

        self.id = opID
        self.inputs: List[Socket] = list()
        self.outputs: List[Socket] = list()

        self._eventLoop: Optional[asyncio.AbstractEventLoop] = None
        self._messageBroker = Operator.MessageBroker(self)

        self.allowNoneMerge = allowNoneMerge  # if false no None values will be passed inside the tuple when combining
        self.pipelineBreaker = pipelineBreaker  # If this forces the children to be of a separate stream
        self.staticDataObject = staticDataObject  # If no deep copy of the object should occur in transmit & display
        self._supportDebugging = supportsDebugging  # If this operator does support debugging

        self._runtimeCreated = False

        # Setup utils

        self._monitor = None
        self._debugger = None
        self._advisor = None

        if config.MONITORING_ENABLED:
            from spe.runtime.monitor.operatorMonitor import OperatorMonitor
            self._monitor = OperatorMonitor(self)

        if config.DEBUGGER_ENABLED:
            from spe.runtime.debugger.operatorDebugger import OperatorDebugger
            self._debugger = OperatorDebugger(self)

        # Determine operator type

        from spe.pipeline.operators.source import Source

        if isinstance(self, Source):
            self._operatorType = OperatorType.SOURCE
        else:
            self._operatorType = OperatorType.DEFAULT

        self._configureSockets(socketsIn, socketsOut)

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

    def onExecutionError(self, error: Optional[str] = None):
        T, V, TB = sys.exc_info()

        # Extract error msg from exception if error txt is not set
        if error is None:
            res = traceback.format_exception_only(T, V)

            error = res[len(res) - 1] + "\n".join(res[:len(res) - 1])

        # Send error
        if self._monitor is not None:
            self._monitor.notifyError(error)

        # Print exception
        if T is not None:
            logging.log(logging.ERROR, traceback.format_exc())

        # Register exceptions produced during actual execution of the operator for debug
        if self.isDebuggingEnabled() and getHistoryState() == HistoryState.INACTIVE:
            ls = self.getDebugger().getLastStep()
            if ls is not None and ls.type == DebugStepType.ON_OP_EXECUTED:
                ls.debugTuple.registerAttribute("opExError", error)

    def exportOperatorData(self) -> dict:
        from spe.pipeline.operators.operatorDB import getPathByOperator

        def getID(operator: Operator):
            return {"id": operator.id, "path": getPathByOperator(type(operator))}

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

    def getInput(self, socketID) -> Optional[Socket]:
        if socketID >= len(self.inputs):
            return None

        return self.inputs[socketID]

    def getOutput(self, socketID) -> Optional[Socket]:
        if socketID >= len(self.outputs):
            return None

        return self.outputs[socketID]

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

    # -------------------------- PIPE DEBUGGER -------------------------

    def isDebuggingEnabled(self, checkSupported: bool = True):
        en = self._debugger is not None and isDebuggerEnabled()

        return en if not checkSupported else en and checkSupported and self.isDebuggingSupported()

    def isDebuggingSupported(self):
        return self._supportDebugging

    def onHistoryContinuation(self, step: DebugStep):
        # Executed when the history is continued and
        # before cont functions of DebugSteps are executed
        # May be overriden by operators to add custom logic
        ...

    # ---

    async def _debugProcessTuple(self, _tuple: Tuple):
        return await self._debugger.registerStep(DebugStepType.PRE_TUPLE_PROCESSED,
                                                 self._debugger.getDT(_tuple),
                                                 undo=lambda pT, nT: self._eventListener.execute(self.EVENT_TUPLE_PRE_PROCESSED, [pT]),
                                                 redo=lambda pT, nT: self._eventListener.execute(self.EVENT_TUPLE_PRE_PROCESSED, [nT]),
                                                 cont=self._onOperatorExecute)

    async def _debugExecuteOperator(self, _tuple: Tuple):
        resTuple = self.createTuple(())  # Required to have access to result tuple

        return await self._debugger.registerStep(DebugStepType.ON_OP_EXECUTED,
                                                 DebugTuple(self._debugger, resTuple),
                                                 undo=lambda pT, nT: self._undoRedoExecute(True, nT),
                                                 redo=lambda pT, nT: self._undoRedoExecute(False, nT),
                                                 cont=lambda rT: self._contExecute(rT))

    async def _contExecute(self, rT: Tuple):
        exTime = self._debugger.getDT(rT).getAttribute("exTime")

        if exTime is None:  # onTupleProcessed was never called with this tuple (ex returned None)
            return

        await self._onTupleProcessed(rT, exTime)

    def _undoRedoExecute(self, undo: bool, tup: Tuple):
        dt = self.getDebugger().getDT(tup)

        err = dt.getAttribute("opExError")
        if err is not None:
            self.onExecutionError(err)

        if undo:
            self._onExecutionUndo(tup)
        else:
            self._onExecutionRedo(tup)

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
                                                 undo=lambda prevT, nT: self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [prevT, 0]),
                                                 redo=lambda pT, nextT: self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [nextT, 0]),
                                                 cont=self._distributeTuple)

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
                                                 undo=lambda pT, nextTuple: self._undoRedoDistribute(True, nextTuple),
                                                 redo=lambda pT, nextTuple: self._undoRedoDistribute(False, nextTuple),
                                                 cont=None)

    # ----------------------------------------------------------------

    def createTuple(self, data: tuple) -> Tuple:
        return Tuple(data, self)

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
            return None

        if not self.staticDataObject:
            # Creates a copy of the input data to not impact previous DTs or parallel executions
            # Premise: The internal tuple data will never change before or after this execute call
            tupleIn = tupleIn.clone(True)

            if not self.isRunning():
                return None

        try:
            # Execute real operator task in parallel
            # Care: For CPU heavy tasks a ProcessPoolExecutor would be more suitable
            # However, data share / copy needs to be handled in this case
            # None uses the asyncio default ThreadPoolExecutor (which shares GLI)
            cpuStartTime = Timer.currentTime()

            tupleNew = await self._eventLoop.run_in_executor(None, self._execute, tupleIn)

            if tupleNew is None:
                return

            cpuStopTime = Timer.currentTime()

            if self.isDebuggingEnabled():
                # Adjust already created result tuple, required to access new data in continuation
                # For long-running operators, it is important to pin to DT to not reload it from DISK
                dt = self._getExecuteDT()
                dt.setTupleData(tupleNew.data, True)
                tupleNew = dt.getTuple()

            # Care: Long running operators might trigger this debugMethod while history is already traversed
            await self._onTupleProcessed(tupleNew, cpuStopTime - cpuStartTime)
        except Exception:
            self.onExecutionError()

    @debugMethod(_debugOnTupleProcessed)
    async def _onTupleProcessed(self, tupleIn: Tuple, executionTime: float):
        self._eventListener.execute(self.EVENT_TUPLE_PROCESSED, [tupleIn, executionTime])

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
    def setData(self, data: json):
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

            onOpMessageQueueChanged(self._operator)

        # -------------------------------- DEBUGGER --------------------------------

        def getMessageCount(self):
            return [len(q) for q in self._messageQueue]

        def undoReceiveTuple(self, t: Tuple):
            self._messageQueue[t.socketID].pop()

            self._totalMessages -= 1

            if self._totalMessages == 0:
                self._queueEvent.clear()

            onOpMessageQueueChanged(self._operator)

        async def _debugProcessTuple(self, resTuple: Tuple):
            return await self._operator.getDebugger().registerStep(DebugStepType.ON_STREAM_PROCESS_TUPLE,
                                                                   DebugTuple(self._operator.getDebugger(), resTuple),
                                                                   undo=lambda pT, nT: self._undoProcessElement(nT),
                                                                   redo=lambda pT, nT: self._createMessageTuple(),
                                                                   cont=self._operator._processTuple)

        def _undoProcessElement(self, processedTuple: Tuple):
            for i in range(len(processedTuple.data)):
                data = processedTuple.data[i]

                # If we have real data or None in case it's not a dummy None added by allowNoneMerge
                if data is not None or not self._operator.allowNoneMerge:
                    self._messageQueue[i].appendleft(processedTuple.data[i])

                    self._totalMessages += 1

            onOpMessageQueueChanged(self._operator)

        # --------------------------------------------------------------------------

        async def _processLoop(self):
            try:
                while self._operator.isRunning():
                    while self._totalMessages > 0:
                        # Check if it is possible to process a tuple

                        canProcessTuple = True
                        for qID in range(len(self._operator.inputs)):
                            q = self._messageQueue[qID]
                            if len(q) == 0 and not self._operator.allowNoneMerge:
                                canProcessTuple = False

                                break

                        if not canProcessTuple:
                            break

                        resTuple = self._operator.createTuple(())

                        await self._processTuple(resTuple)

                    if not self._operator.isRunning():  # Closed
                        return

                    self._queueEvent.clear()

                    await self._queueEvent.wait()

                    if self._operator.isDebuggingEnabled():
                        # In case the history is paused, wait for continuation.
                        # This is crucial since redo receive tuple sets queueEvent and triggers processing.
                        await self._operator.getDebugger().getDebugger().getHistoryAsyncioEvent().wait()
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
                elif self._operator.allowNoneMerge:
                    messageElements.append(None)
                else:
                    raise Exception("No elements in message queue for op " + str(self._operator.id) + " and socket " + str(qID) + "!")

            onOpMessageQueueChanged(self._operator)

            return tuple(messageElements)

        # --------------------------------------------------------------------------

        def createRuntime(self, eventLoop: asyncio.AbstractEventLoop):
            self._queueEvent = asyncio.Event()

            self._futureThread = asyncio.ensure_future(self._processLoop(), loop=eventLoop)

        def destroyRuntime(self, eventLoop: asyncio.AbstractEventLoop):
            if eventLoop.is_running() and self._futureThread is not None:
                self._futureThread.cancel()

            self._futureThread = None

            self._queueEvent = None
