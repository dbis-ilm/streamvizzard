import asyncio
import logging
import os.path
import shutil
import threading
import time
import traceback
from math import sqrt
from typing import List, Dict, Optional, Callable

from spe.pipeline.operators.operator import Operator
from spe.pipeline.operators.source import Source
from spe.pipeline.pipeline import Pipeline
from spe.runtime.debugger.debugStep import DebugStepType
from spe.runtime.runtimeManager import RuntimeManager
from spe.runtime.simulation.simulationDummyData import SimulationDummyData
from spe.runtime.simulation.simulator.petriNet.ilmCompiler import IlmCompiler
from spe.runtime.simulation.simulator.petriNet.simulationImporter import importSimulationResults, \
    OperatorSimulationResEntry, \
    OperatorSimulationResultType
from spe.runtime.simulation.simulator.pipelineSimulator import PipelineSimulator, PipelineSimulationMode
from spe.common.timer import Timer
from spe.common.tuple import Tuple


class PetriNetPipelineSim(PipelineSimulator):
    def __init__(self, pipeline: Pipeline, runtimeManager: RuntimeManager):
        super(PetriNetPipelineSim, self).__init__(pipeline, runtimeManager, PipelineSimulationMode.PETRINET)

        self._performEvaluation = False  # If the provided real execution results should be compared to the simulated
        self._clearResultFolderOnStart = False

        self._simResPath = ""

    def start(self, duration: float, sourceCfgs: Dict, metaData: Dict, settingsCallback: Optional[Callable]):
        self._simResPath = metaData["resPath"]

        if self._clearResultFolderOnStart:
            self._emptyResultFolder()

        self._prepareOperators()

        self._startSimulation(duration, settingsCallback)

        compiler = IlmCompiler(self.pipeline, metaData["realOpNames"], metaData["costModelPath"])
        compiler.compile(duration, sourceCfgs, metaData["ilmPath"])

        threading.Thread(target=self._startThread, daemon=True).start()

    def _emptyResultFolder(self):
        # Empty result folder
        for root, dirs, files in os.walk(self._simResPath):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

    def _startThread(self):
        found = False

        while True and self.manager.isRunning():
            if os.path.exists(os.path.join(self._simResPath, "results.log")):
                found = True

                break

            time.sleep(0.25)

        if not found:
            return

        simulationSteps = importSimulationResults(self._simResPath)

        self._applySimulationResults(simulationSteps)

    def _prepareOperators(self):
        # Replace all execute functions with dummy functions

        async def _dummyBrokerLoop():
            pass

        for op in self.pipeline.getAllOperators():
            op._execute = lambda *args: None
            op._onExecutionUndo = lambda tup: None
            op._onExecutionRedo = lambda tup: None
            op.getBroker()._processLoop = _dummyBrokerLoop

            if isinstance(op, Source):
                op._runSource = lambda *args: None

    def _applySimulationResults(self, stepList: List[OperatorSimulationResEntry]):
        if not self.manager.isRunning():
            print("Pipeline ist not running!")

            self._onError()

            return

        if self._performEvaluation:
            self._evaluatePetriNetSim(stepList)

        asyncio.run_coroutine_threadsafe(self._createHistory(stepList), loop=self.manager.getEventLoop())

    def _evaluatePetriNetSim(self, stepList: List[OperatorSimulationResEntry]):
        simOpTP = dict()

        # --- Simulate---

        initialTime = dict()

        for step in stepList:
            if step.resType == OperatorSimulationResultType.EXECUTION:
                oldTP = simOpTP.get(step.opID)

                it = initialTime.get(step.opID)
                if it is None:  # First entries needs to be skipped since real values start at second
                    initialTime[step.opID] = step.time
                    continue

                if oldTP is not None:
                    lastElm = oldTP[len(oldTP) - 1]
                    timeDif = step.time - it

                    tp = (lastElm[0] + 1) / timeDif if timeDif != 0 else 0

                    simOpTP[step.opID].append((lastElm[0] + 1, tp))
                else:
                    timeDif = step.time - it
                    tp = 1 / timeDif if timeDif != 0 else 0

                    simOpTP[step.opID] = [(1, tp)]

        # --- Recorded ---

        import os
        from pathlib import Path

        realOpTP = dict()

        for file in os.listdir("E:/PHD/PetriNetSim/realTPs"):
            fileName = Path(file).stem

            opID = int(fileName)

            with open("E:/PHD/PetriNetSim/realTPs/" + fileName + ".txt") as fileRaw:
                initialTime = 0

                for line in fileRaw:
                    ln = line.strip().split(",")

                    timestamp = float(ln[1])

                    if initialTime == 0:
                        initialTime = timestamp
                        continue

                    oldTP = realOpTP.get(opID)

                    if oldTP is not None:
                        timeDif = timestamp - initialTime

                        lastElm = oldTP[len(oldTP) - 1]

                        tp = (lastElm[0] + 1) / timeDif if timeDif != 0 else 0

                        realOpTP[opID].append((lastElm[0] + 1, tp, timestamp))
                    else:
                        timeDif = timestamp - initialTime
                        tp = 1 / timeDif if timeDif != 0 else 0

                        realOpTP[opID] = [(1, tp, timestamp)]

        # --- Calc delta ---

        deltas = []

        for op in self.pipeline.getAllOperators():
            # if op.id == 9 or op.id == 39 or op.id == 42:
            #    continue

            realVals = realOpTP.get(op.id)
            simVals = simOpTP.get(op.id)

            if realVals is None or simVals is None:
                continue

            delta = 0

            for vID in range(len(simVals)):
                if len(realVals) <= vID:
                    break

                sim = simVals[vID]
                real = realVals[vID]

                dif = pow(sim[1] - real[1], 2)
                delta += dif

                deltas.append((real[2], dif, real[1]))

            print("Delta " + str(op.id) + ": " + str(sqrt(delta / len(simVals))))

        deltas.sort(key=lambda x: x[0])

        totalDelta = 0
        totalCount = 0
        totalReal = 0

        with open('E:/PHD/PetriNetSim/evaluation.txt', 'w') as f:
            firstTime = -1

            f.write("x,y\n")

            i = 0
            for d in deltas:
                i += 1
                timestamp = d[0]

                if firstTime == -1:
                    firstTime = timestamp

                totalDelta += d[1]
                totalCount += 1
                totalReal += d[2]

                mean = totalReal / totalCount

                # Store normalized rmse (every 4th entry)
                if i % 4 == 0:
                    f.write(str(timestamp - firstTime) + "," + str(sqrt(totalDelta / totalCount) / mean) + "\n")
                    i = 0

    async def _createHistory(self, stepList: List[OperatorSimulationResEntry]):
        opTupLookup: Dict[int, Tuple] = dict()

        t = time.time()

        def createTuple(operator: Operator, s: OperatorSimulationResEntry) -> Tuple:
            if isinstance(s.value, tuple):
                res = []

                for elID in range(len(s.value)):
                    res.append(SimulationDummyData(s.value[elID], s.dataSize[elID]))

                newTup = operator.createTuple(tuple(res))
            else:
                newTup = operator.createTuple((SimulationDummyData(s.value, s.dataSize),))

            opTupLookup[operator.id] = newTup

            newTup.eventTime = s.getRealTime()

            return newTup

        def adaptTime(operator: Operator, stepType: DebugStepType, s: OperatorSimulationResEntry):
            lastS = operator.getDebugger().getLastStepForIdentifier(stepType)

            if lastS is not None:
                lastS.time = s.getRealTime()

        try:
            for step in stepList:
                if not self.manager.isRunning():  # In case pipeline is stopped during loading
                    return

                op = self.pipeline.getOperator(step.opID)

                # print(str(op.id) + ":" + str(step.resType) + " - > " + str(step.getRealTime()))

                if op is None:
                    print("Operator " + str(step.opID) + " not found in pipeline!")

                    continue

                if not op.isDebuggingEnabled():
                    print("Debugger is not enabled for operator " + str(op.id))

                    continue

                # TODO: SOCKET NUMBERS WRONG?
                if step.resType == OperatorSimulationResultType.READY:
                    # When a new tuple can be processed by the operator

                    tupData = op.getBroker()._createMessageTuple()
                    newTup = op.createTuple(tupData)

                    opTupLookup[op.id] = newTup

                    await op. getBroker()._debugProcessTuple(newTup)

                    adaptTime(op, DebugStepType.ON_STREAM_PROCESS_TUPLE, step)

                    await op._debugProcessTuple(newTup)

                    adaptTime(op, DebugStepType.PRE_TUPLE_PROCESSED, step)
                elif step.resType == OperatorSimulationResultType.EXECUTION:
                    # When an operator executes his function

                    ds = op.getDebugger().getLastStepForIdentifier(DebugStepType.PRE_TUPLE_PROCESSED)
                    exTime = step.getRealTime() - ds.time if ds is not None else 0

                    await op._debugExecuteOperator(opTupLookup[op.id])

                    adaptTime(op, DebugStepType.ON_OP_EXECUTED, step)

                    dt = op.getDebugger().getLastDTForStep(DebugStepType.ON_OP_EXECUTED)
                    dt.setTupleData((SimulationDummyData(step.value, step.dataSize),), True)

                    resTup = dt.getTuple()
                    resTup.eventTime = step.getRealTime()

                    opTupLookup[op.id] = resTup

                    await op._debugOnTupleProcessed(resTup, exTime)

                    adaptTime(op, DebugStepType.ON_TUPLE_PROCESSED, step)

                    op.getEventListener().execute(Operator.EVENT_TUPLE_PROCESSED, [resTup, exTime])
                elif step.resType == OperatorSimulationResultType.PRODUCE:
                    # When the data is produced by a source

                    if isinstance(op, Source):
                        ds = op.getDebugger().getLastStepForIdentifier(DebugStepType.ON_SOURCE_PRODUCED_TUPLE)
                        exTime = step.time - ds.time if ds is not None else 0

                        prodTuple = createTuple(op, step)

                        await op._debugProduceTuple(prodTuple, exTime)

                        adaptTime(op, DebugStepType.ON_SOURCE_PRODUCED_TUPLE, step)

                        op.getEventListener().execute(Operator.EVENT_TUPLE_PROCESSED, [prodTuple, exTime])
                elif step.resType == OperatorSimulationResultType.CONNECTOR:
                    # When a tuple is transmitted to succeeding operators

                    # Retrieve existing tuple and set the correct data
                    lid = DebugStepType.ON_TUPLE_PROCESSED if not op.isSource() else DebugStepType.ON_SOURCE_PRODUCED_TUPLE

                    ls = op.getDebugger().getLastStepForIdentifier(lid)
                    lt = ls.debugTuple.getTuple()

                    lt.data = createTuple(op, step).data  # Value of step needs to be in tuple format

                    await op._debugDistribute(lt)

                    adaptTime(op, DebugStepType.ON_TUPLE_TRANSMITTED, step)

                    # Add data to target operators
                    for outID in range(len(op.outputs)):
                        for con in op.outputs[outID].getConnections():
                            otherOp = con.input.op

                            newTup = op.createTuple((lt.data[con.output.id],))
                            newTup.socketID = con.input.id
                            newTup.eventTime = step.getRealTime()

                            # Adapt timer for correct TP calculation
                            ct = Timer.currentTime()
                            Timer.setTime(step.getRealTime())
                            con.onTupleTransmitted(lt)
                            Timer.setTime(ct)

                            otherOp.getBroker().receiveTuple(newTup)

        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            self._onError()

        # Pause execution for debugging - call from thread since we are inside async loop
        threading.Thread(target=self.manager.gateway.getDebugger().changeDebuggerState, args=(True, None)).start()

        print("DONE in " + str((time.time() - t) * 1000))
