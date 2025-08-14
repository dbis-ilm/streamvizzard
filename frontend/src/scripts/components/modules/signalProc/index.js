import Operators from "@/scripts/components/modules/signalProc/operators";
import Sources from "@/scripts/components/modules/signalProc/sources";
import {MonitorDataType} from "@/scripts/components/monitor/MonitorDataType";
import Rete from "rete";
import Scatterplot from "@/components/features/monitor/displays/ScatterplotDT";

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

export const signalSocket = new Rete.Socket('Signal');

let getSockets = () => {
    return [signalSocket];
}

//MONITOR DATA TYPES

export const SIGNAL_DT = new MonitorDataType("SIGNAL", "Signal");
SIGNAL_DT.registerDisplayMode(0, "Time-Series", Scatterplot, {"yrange": [-30000, 30000], "ytitle": "Amplitude", "yvisible": true});
SIGNAL_DT.registerDisplayMode(1, "PSD Welch ", Scatterplot, {"yrange": [0, 1000], "xtitle": "HZ", "xvisible": true, "yvisible": true});

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
