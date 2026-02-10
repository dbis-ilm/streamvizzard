import Operator from "@/scripts/pipeline/operators/modules/base/operators";
import Source from "@/scripts/pipeline/operators/modules/base/sources";
import Sinks from "@/scripts/pipeline/operators/modules/base/sinks";
import {
    DT_Literal,
    DT_Scatterplot,
    MonitorDataType,
    MonitorDisplayMode
} from "@/scripts/features/monitor/MonitorDataType";

import {SocketType} from "@/scripts/pipeline/SvSocket";

let getComponents = () => {
    const ops = Operator.getComponents(["Operators"])
        .concat(Source.getComponents(["Sources"]))
        .concat(Sinks.getComponents(["Sinks"]));

    for (const o in ops) {
        const path = ops[o].path;
        ops[o].path = [Module.name].concat(path);
        ops[o].contextPath = [Module.displayName].concat(path);
        ops[o].bgColor = Module.bgColor;
    }

    return ops;
}

// SOCKETS

export const numSocket = new SocketType("Number");
export const boolSocket = new SocketType("Boolean");
export const strSocket = new SocketType("String");
export const arraySocket = new SocketType("Array");
export const windowSocket = new SocketType("Window");

let getSockets = () => {
    return [numSocket, boolSocket, strSocket, arraySocket, windowSocket];
}

//MONITOR DATA TYPES

export const NUMBER_DT = new MonitorDataType("NUMBER", "Number");
NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(0, "Raw", DT_Literal));
NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(1, "Time-Series", DT_Scatterplot, {"useBuffer": true, "maxBufferElements": 25, "xvisible": false}));

export const STRING_DT = new MonitorDataType("STRING", "String");
STRING_DT.registerDisplayMode(new MonitorDisplayMode(0, "Raw", DT_Literal));
STRING_DT.registerDisplayMode(new MonitorDisplayMode(1, "Length", DT_Literal));

export const ARRAY_NUMBER_DT = new MonitorDataType("ARRAY_NUMBER", "Num Array")
ARRAY_NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(0, "Count", DT_Literal));
ARRAY_NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(1, "Time-Series", DT_Scatterplot, {"useXDif": true, "xtitle": "Tuple #"}));

export const WINDOW_NUMBER_DT = new MonitorDataType("WINDOW_NUMBER", "Num Window")
WINDOW_NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(0, "Count", DT_Literal));
WINDOW_NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(1, "Time-Series", DT_Scatterplot, {"useXDif": true, "xtitle": "Tuple #"}));

let getDataTypes = () => {
    return [NUMBER_DT, STRING_DT, ARRAY_NUMBER_DT, WINDOW_NUMBER_DT];
}

// -------------------------------------------------------------------------

export default {
    Operator, Source, Sinks, getComponents, getSockets, getDataTypes
}

export const Module = {
    name: "Base",
    displayName: "Base",
    bgColor: "radial-gradient(circle, rgb(164, 234, 255) 0%, rgb(130, 226, 255) 100%)"
}
