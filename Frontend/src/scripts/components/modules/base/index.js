import Rete from "rete";

import Operator from "@/scripts/components/modules/base/operators";
import Source from "@/scripts/components/modules/base/sources";
import {MonitorDataType} from "@/scripts/components/monitor/MonitorDataType";
import LiteralDT from "@/components/templates/displays/LiteralDT";
import Scatterplot from "@/components/templates/displays/ScatterplotDT";
import CanvasDT from "@/components/templates/displays/CanvasDT";

let getComponents = () => {
    const ops =  Operator.getComponents(["Operators"])
        .concat(Source.getComponents(["Sources"]));

    for (const o in ops) {
        const path = ops[o].path;
        ops[o].path = [Module.name].concat(path);
        ops[o].contextPath = [Module.displayName].concat(path);
        ops[o].bgColor = Module.bgColor;
    }

    return ops;
}

// SOCKETS

export const numSocket = new Rete.Socket('Number');
export const strSocket = new Rete.Socket('String');
export const primitiveSocket = new Rete.Socket('Primitive');

let getSockets = () => {
    return [numSocket, strSocket, primitiveSocket];
}

numSocket.combineWith(primitiveSocket);
strSocket.combineWith(primitiveSocket);

//MONITOR DATA TYPES

export const NUMBER_DT = new MonitorDataType("NUMBER", "Number");
NUMBER_DT.registerDisplayMode(0, "Raw", LiteralDT);
NUMBER_DT.registerDisplayMode(1, "Time-Series", Scatterplot, {"useBuffer": true, "maxBufferElements": 25, "xvisible": false});

export const STRING_DT = new MonitorDataType("STRING", "String");
STRING_DT.registerDisplayMode(0, "Raw", LiteralDT);
STRING_DT.registerDisplayMode(1, "Length", LiteralDT);

export const ARRAY_NUMBER_DT = new MonitorDataType("ARRAY_NUMBER", "Num Array")
ARRAY_NUMBER_DT.registerDisplayMode(0, "Count", LiteralDT);
ARRAY_NUMBER_DT.registerDisplayMode(1, "Time-Series", Scatterplot, {"useXDif": true, "xtitle": "Δs"});

export const WINDOW_NUMBER_DT = new MonitorDataType("WINDOW_NUMBER", "Num Window")
WINDOW_NUMBER_DT.registerDisplayMode(0, "Count", LiteralDT);
WINDOW_NUMBER_DT.registerDisplayMode(1, "Time-Series", Scatterplot, {"useXDif": true, "xtitle": "Δs"});

export const FIGURE_DT = new MonitorDataType("FIGURE", "Figure");
FIGURE_DT.registerDisplayMode(0, "Canvas", CanvasDT);

let getDataTypes = () => {
    return [NUMBER_DT, STRING_DT, ARRAY_NUMBER_DT, WINDOW_NUMBER_DT, FIGURE_DT];
}

// -------------------------------------------------------------------------

export default {
    Operator, Source, getComponents, getSockets, getDataTypes
}

export const Module = {
    name: "Base",
    displayName: "Base",
    bgColor: "radial-gradient(circle, rgba(130, 226, 255, 0.75) 0%, rgba(130, 226, 255, 0.9) 100%)"
}
