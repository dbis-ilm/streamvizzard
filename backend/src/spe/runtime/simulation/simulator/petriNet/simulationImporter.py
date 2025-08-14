import logging
import os
import traceback
from datetime import date
from enum import Enum
from pathlib import Path
from typing import List, Optional

COLUMN_SEPARATOR = "\t"
TIMESCALE_FACTOR = 1000000  # s -> us


class OperatorSimulationResultType(Enum):
    READY = "ready"
    EXECUTION = "execution"
    CONNECTOR = "connector"
    PRODUCE = "postExecution"

    @staticmethod
    def parse(sm: str):
        for v in OperatorSimulationResultType:
            if v.value == sm:
                return v

        return None


class OperatorSimulationResEntry:
    def __init__(self, opID: int, resType: OperatorSimulationResultType, time: float, dataSize, value, meta):
        self.opID = opID
        self.resType = resType
        self.time = time  # In seconds
        self.dataSize = dataSize  # Can be a tuple of elements for CONNECTOR
        self.value = value  # Can be a tuple of elements for CONNECTOR

        self.meta = meta  # Out Socket ID for CONNECTOR

        # Add minimal delay, to ensure fixed order for previous connector transitions
        if resType == OperatorSimulationResultType.READY:
            self.time += 0.00001

    def getRealTime(self):
        # Returns time in seconds
        return self.time / TIMESCALE_FACTOR


def importSimulationResults(folderPath: str) -> List[OperatorSimulationResEntry]:
    res = []

    for file in os.listdir(folderPath):
        if file.endswith('.csv'):

            fullPath = os.path.join(folderPath, file)
            fileName = Path(file).stem

            metaData = None

            if "_to_" in fileName:
                s = fileName.split("_to_")

                op1 = s[0].split(".")
                # op2 = s[1].split(".")

                op1ID = int(op1[0].split("__")[1])
                # op2ID = int(op2[0].split("__")[1])

                op1Port = int(op1[1].split("_")[1])
                # op2Port = int(op2[1].split("_")[1])

                resType = OperatorSimulationResultType.CONNECTOR
                opID = op1ID
                metaData = op1Port
            elif "__" in fileName:
                p = fileName.split("__")[1].split("_")
                opID = int(p[0])
                identifier = p[1]

                resType = OperatorSimulationResultType.parse(identifier)
            else:  # Other files we are not interested in
                continue

            runs = []
            currentRun = None

            header = None

            with open(fullPath) as fileRaw:
                for line in fileRaw:
                    ln = line.rstrip()

                    # First line is header
                    if header is None:
                        header = ln

                        continue

                    if ln == header:
                        if currentRun is not None and len(currentRun) > 0:
                            runs.append(currentRun)

                            break
                        currentRun = []
                    else:
                        pr = _processLine(ln, opID, resType, metaData)
                        if pr is None:
                            continue

                        currentRun.append(pr)

                runs.append(currentRun)

            res.extend(runs[0])

    res.sort(key=lambda x: x.time)

    # TODO: MERGE CONNECTOR ENTRIES THAT HAVE MULTIPLE OUTS!

    return res


lastTime = ""


def _processLine(line: str, opID: int, resType: OperatorSimulationResultType, metaData) -> Optional[OperatorSimulationResEntry]:
    split = line.split(COLUMN_SEPARATOR)

    global lastTime
    if lastTime == split[0]:
        print("SAME TIMESTAMP: " + str(lastTime) + ":" + str(opID) + ":" + str(resType))

    lastTime = split[0]

    time = _parseTimestamp(split[0])

    dataSize = int(split[1])
    val = split[2]

    if time is None:
        return None

    e = OperatorSimulationResEntry(opID, resType, time, dataSize, val, metaData)

    return e


def _parseTimestamp(timeStamp: str):
    if len(timeStamp.strip()) == 0:
        return None
    try:
        timestamp = timeStamp.split("@")
        time = timestamp[0]
        dayFormat = timestamp[1].split("/")

        day = int(dayFormat[1])
        month = int(dayFormat[0])
        year = int(dayFormat[2])

        d0 = date(year + 2000, month, day)
        d1 = date(1, 12, 31)

        delta = d0 - d1
        deltaSeconds = delta.days * 24 * 60 * 60

        times = time.split(":")

        hours = int(times[0])
        minutes = int(times[1])
        secs = int(times[2])

        us = (((hours * 60) + minutes) * 60) + secs + deltaSeconds

        return us
    except Exception:
        print("Couldn't parse value: " + timeStamp)
        logging.log(logging.ERROR, traceback.format_exc())
        return None
