from __future__ import annotations

from typing import Dict, List
from typing import TYPE_CHECKING

from spe.common.serialization.jsonSerialization import fastSerializeToJSONBytes
from spe.common.timer import Timer

if TYPE_CHECKING:
    from spe.pipeline.connection import Connection
    from spe.pipeline.operators.operator import Operator


def createOperatorData(operators: List[Operator]) -> bytes:
    obj = {"cmd": "opMonitorData"}

    ops = []

    for op in operators:
        monitor = op.getMonitor()

        resData: Dict[str, Dict] = dict()

        resData["id"] = op.id
        resData["data"] = monitor.getDisplayData()
        resData["exTime"] = monitor.getAvgExecutionTime()
        resData["dataSize"] = monitor.getAvgDataSize()
        resData["totalTuples"] = monitor.getTotalTuples()
        resData["time"] = monitor.getLastProcessTime()

        ops.append(resData)

    obj["ops"] = ops

    return fastSerializeToJSONBytes(obj)


def createConnectionData(connections: List[Connection]) -> bytes:
    obj = {"cmd": "conMonitorData"}

    cons = []

    for con in connections:
        monitor = con.getMonitor()

        cons.append({
            "id": con.id,
            "tp": monitor.getAvgThroughput(),
            "total": monitor.getTotalTuples(),
            "time": Timer.currentTime()
        })

    obj["cons"] = cons

    return fastSerializeToJSONBytes(obj)


def createMessageBrokerData(operators: List[Operator]) -> bytes:
    obj = {"cmd": "msgBroker"}

    ops = []

    for op in operators:
        ops.append({"id": op.id,
                    "broker": {"msg": op.getBroker().getMessageCount(),
                               "max": 100}})  # TODO: LATER USE SOME LIMITS FOR MESSAGES?

    obj["ops"] = ops

    return fastSerializeToJSONBytes(obj)
