from __future__ import annotations

import os.path
import timeit
from typing import List, TYPE_CHECKING, Dict, Optional

from analysis.costModel.executionRecording import ExecutionRecording, RecordingParam
from utils.fileUtils import getStructuredOperatorPath
from analysis.costModel.costModel import CostModelTarget, CostModelEnv, CostModelMetaData

if TYPE_CHECKING:
    from analysis.costModel.configurations.costModelOpSetups import CostModelOpCfg
    from spe.common.tuple import Tuple


class OperatorEntry:
    def __init__(self, opCfg: CostModelOpCfg):
        self.opCfg = opCfg

        self.recordings: Dict[CostModelEnv, ExecutionRecording] = dict()

    def collectRecordings(self, recordingsPath: str, forceRecordings: bool = False):
        """ forceRecordings if all currently stored recordings should be ignored to force a re-execution of the operators. """

        parentFolder, opName = getStructuredOperatorPath(type(self.opCfg.operator), rootFolder=recordingsPath, mkdirs=True)

        # Execute operator if desired

        if self.opCfg.runCfg is not None:
            recPath = os.path.join(parentFolder, f"{opName}_{CostModelEnv.SV_CPU.name}.svrec")

            if not os.path.exists(recPath) or forceRecordings:  # Recalculate recordings
                self._runOperatorCPUExecution(recPath)

        # Load all requested recordings

        for target in self.opCfg.targets:
            if target.env in self.recordings:
                continue

            recPath = os.path.join(parentFolder, f"{opName}_{target.env.name}.svrec")

            if os.path.exists(recPath):
                entries: List[ExecutionRecording.Entry] = []

                with open(recPath, 'r') as f:
                    for line in f:
                        entries.append(ExecutionRecording.Entry.fromJSON(line))

                self.recordings[target.env] = ExecutionRecording(target.env, entries)

    def getTarget(self, env: CostModelEnv, target: CostModelTarget):
        for t in self.opCfg.targets:
            if t.env == env and t.target == target:
                return t

        return None

    def getRecording(self, env: CostModelEnv) -> Optional[ExecutionRecording]:
        return self.recordings.get(env, None)

    def _runOperatorCPUExecution(self, recordingsFilePath: str) -> ExecutionRecording:
        runCfg = self.opCfg.runCfg

        entries: List[ExecutionRecording.Entry] = []

        with open(recordingsFilePath, 'w') as f:
            for iteration in range(runCfg.iterations):
                inputTuple = self.opCfg.operator.createTuple(runCfg.dataLoader(iteration))
                data = runCfg.dataRetriever(iteration) if runCfg.dataRetriever is not None else None

                if data is not None:
                    self.opCfg.operator.setData(data)

                inDataSize = inputTuple.calcMemorySize()

                outSize, exTime = self._performCPUExecution(inputTuple)

                if iteration < runCfg.warmUp:
                    continue

                metaData = CostModelMetaData.construct(inDataSize)

                params = runCfg.paramRetriever(inputTuple.data, self.opCfg.operator)
                params.extend(RecordingParam.getMetaDataParams(metaData))

                r = ExecutionRecording.Entry(inDataSize, params, outSize, exTime)

                entries.append(r)

                if f is not None:  # Write result to file
                    f.write(r.toJSON() + "\n")
                    f.flush()

        return ExecutionRecording(CostModelEnv.SV_CPU, entries)

    def _performCPUExecution(self, inputData: Tuple) -> tuple[float, float]:
        runCfg = self.opCfg.runCfg

        totalRT = 0
        res = None

        for rep in range(runCfg.repetitions):
            cpuStartTime = timeit.default_timer()

            res = self.opCfg.operator._execute(inputData)

            cpuStopTime = timeit.default_timer()

            if runCfg.postExecution is not None:
                runCfg.postExecution(self.opCfg.operator)

            processingTime = (cpuStopTime - cpuStartTime)

            totalRT += processingTime

        avgRT = totalRT / runCfg.repetitions

        return res.calcMemorySize(), avgRT
