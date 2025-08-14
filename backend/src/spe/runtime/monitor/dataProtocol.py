from __future__ import annotations

import json
from typing import Dict, List
from typing import TYPE_CHECKING

from spe.common.serialization.jsonSerialization import serializeToJSON

if TYPE_CHECKING:
    from spe.pipeline.connection import Connection
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.monitor.heatmap import HeatmapResult


def createOperatorData(operators: List[Operator]) -> json:
    obj = {"cmd": "opMonitorData"}

    ops = []

    for op in operators:
        monitor = op.getMonitor()

        resData: Dict[str, json] = dict()

        resData["id"] = op.id
        resData["data"] = monitor.getDisplayData()

        ops.append(resData)

    obj["ops"] = ops

    return serializeToJSON(obj)


def createConnectionData(connections: List[Connection]) -> json:
    obj = {"cmd": "conMonitorData"}

    cons = []

    for con in connections:
        monitor = con.getMonitor()

        cons.append({
            "id": con.id,
            "tp": monitor.throughput,
            "total": monitor.totalTuples
        })

    obj["cons"] = cons

    return json.dumps(obj)


def createMessageBrokerData(operators: List[Operator]):
    obj = {"cmd": "msgBroker"}

    ops = []

    for op in operators:
        ops.append({"id": op.id,
                    "broker": {"msg": op.getBroker().getMessageCount(),
                               "max": 100}})  # TODO: LATER USE SOME LIMITS FOR MESSAGES?

    obj["ops"] = ops

    return json.dumps(obj)


def createHeatmapData(hmData: HeatmapResult) -> json:
    obj = {"cmd": "heatmap"}

    ops = []

    for k, v in hmData.opRating.items():
        ops.append({"op": k.id, "rating": v})

    obj["ops"] = ops
    obj["min"] = hmData.minVal
    obj["max"] = hmData.maxVal
    obj["steps"] = hmData.legendSteps

    return json.dumps(obj)
