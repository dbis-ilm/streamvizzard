import Operators from "@/scripts/pipeline/operators/modules/signalProc/operators";
import Sources from "@/scripts/pipeline/operators/modules/signalProc/sources";
import {
    DT_Heatmap,
    DT_Scatterplot, DT_Table,
    MonitorDataType,
    MonitorDisplayMode, TemplateSetting
} from "@/scripts/features/monitor/MonitorDataType";

import {SocketType} from "@/scripts/pipeline/SvSocket";
import NumberDS from "@/components/features/monitor/sidebar/settings/NumberDS.vue";

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
SIGNAL_DT.registerDisplayMode(new MonitorDisplayMode(0, "Time-Series", DT_Scatterplot, {"yrange": [-1, 1], "xtitle": "Sample", "ytitle": "Amplitude", "yvisible": true, "maxBufferElements": 1000},
    () => { return [new TemplateSetting("channel", "Channel", 1, 1, NumberDS, "The channel to plot [1,#channels]. Empty falls back to first channel.")]}));
SIGNAL_DT.registerDisplayMode(new MonitorDisplayMode(1, "PSD Welch ", DT_Scatterplot, {"yrange": [-20, 20], "xtitle": "Frequency (Hz)", "ytitle": "Power (dB)", "xvisible": true, "yvisible": true, "maxBufferElements": 1000},
    () => { return [new TemplateSetting("channel", "Channel", 1, 1, NumberDS, "The channel to plot [1,#channels]. Empty falls back to first channel.")]}));
SIGNAL_DT.registerDisplayMode(new MonitorDisplayMode(2, "Spectrogram", DT_Heatmap, {"xtitle": "Time (s)", "ytitle": "Frequency (Hz)", "ztitle": "Power (dB)", "maxCells": 1000},
    () => { return [new TemplateSetting("channel", "Channel", 1, 1, NumberDS, "The channel to plot [1,#channels]. Empty falls back to first channel.")]}));
SIGNAL_DT.registerDisplayMode(new MonitorDisplayMode(3, "Meta Data", DT_Table));

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
