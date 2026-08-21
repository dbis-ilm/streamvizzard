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
export const windowSocket = new SocketType("Window", true);

let getSockets = () => {
    return [numSocket, boolSocket, strSocket, arraySocket, windowSocket];
}

//MONITOR DATA TYPES

export const NONE_DT = new MonitorDataType("NONE", "Empty Data");
NONE_DT.registerDisplayMode(new MonitorDisplayMode(0, "Raw", DT_Literal));

export const NUMBER_DT = new MonitorDataType("NUMBER", "Number");
NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(0, "Raw", DT_Literal));
NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(1, "Time-Series", DT_Scatterplot, {
    "useBuffer": true,
    "xtitle": "Δs",
    "xvisible": true
}));

export const STRING_DT = new MonitorDataType("STRING", "String");
STRING_DT.registerDisplayMode(new MonitorDisplayMode(0, "Raw", DT_Literal));
STRING_DT.registerDisplayMode(new MonitorDisplayMode(1, "Length", DT_Literal));

export const ARRAY_NUMBER_DT = new MonitorDataType("ARRAY_NUMBER", "Number Array")
ARRAY_NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(0, "Count", DT_Literal, {"exp": "'Array [' + $VAL + ' Numbers]'"}));
ARRAY_NUMBER_DT.registerDisplayMode(new MonitorDisplayMode(1, "Time-Series", DT_Scatterplot, {"xtitle": "Tuple #"}));

export const DICT_INSPECT_DT = new MonitorDataType("DICT_INSPECT", "Dictionary Inspect");
export const ARRAY_INSPECT_DT = new MonitorDataType("ARRAY_INSPECT", "List Inspect");
export const TUPLE_INSPECT_DT = new MonitorDataType("TUPLE_INSPECT", "Tuple Inspect");

let getDataTypes = () => {
    return [NONE_DT, NUMBER_DT, STRING_DT, ARRAY_NUMBER_DT, DICT_INSPECT_DT, ARRAY_INSPECT_DT, TUPLE_INSPECT_DT];
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
