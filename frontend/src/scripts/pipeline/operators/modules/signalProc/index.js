import Operators from "@/scripts/pipeline/operators/modules/signalProc/operators";
import Sources from "@/scripts/pipeline/operators/modules/signalProc/sources";
import {DT_Scatterplot, MonitorDataType, MonitorDisplayMode} from "@/scripts/features/monitor/MonitorDataType";

import {SocketType} from "@/scripts/pipeline/SvSocket";

let getComponents = () => {
    const ops =  Operators.getComponents(["Operators"]).concat(Sources.getComponents(["Sources"]));

    for (const o in ops) {
        const path = ops[o].path;
        ops[o].path = [Module.name].concat(path);
        ops[o].contextPath = [Module.displayName].concat(path);
        ops[o].bgColor = Module.bgColor;
    }

    return ops;
}

//SOCKETS

export const signalSocket = new SocketType("Signal");

let getSockets = () => {
    return [signalSocket];
}

//MONITOR DATA TYPES

export const SIGNAL_DT = new MonitorDataType("SIGNAL", "Signal");
SIGNAL_DT.registerDisplayMode(new MonitorDisplayMode(0, "Time-Series", DT_Scatterplot, {"yrange": [-30000, 30000], "ytitle": "Amplitude", "yvisible": true}));
SIGNAL_DT.registerDisplayMode(new MonitorDisplayMode(1, "PSD Welch ", DT_Scatterplot, {"yrange": [0, 1000], "xtitle": "HZ", "xvisible": true, "yvisible": true}));

let getDataTypes = () => {
    return [SIGNAL_DT];
}

// -------------------------------------------------------------------------

export default {
    Operators, Sources, getComponents, getSockets, getDataTypes
}

export const Module = {
    name: "SignalProc",
    displayName: "Signal Processing",
    bgColor: "radial-gradient(circle, rgb(147, 223, 131) 0%, rgb(104, 221, 79) 100%)"
}
