import Operators from "@/scripts/pipeline/operators/modules/imageproc/operators";
import Sources from "@/scripts/pipeline/operators/modules/imageproc/sources";
import {
    DT_Image, DT_Literal,
    DT_Scatterplot,
    MonitorDataType,
    MonitorDisplayMode
} from "@/scripts/features/monitor/MonitorDataType";

import {SocketType} from "@/scripts/pipeline/SvSocket";


let getComponents = () => {
    const ops = Operators.getComponents(["Operators"])
        .concat(Sources.getComponents(["Sources"]));

    for (const o in ops) {
        const path = ops[o].path;
        ops[o].path = [Module.name].concat(path);
        ops[o].contextPath = [Module.displayName].concat(path);
        ops[o].bgColor = Module.bgColor;
    }

    return ops;
}

//SOCKETS

export const imgSocket = new SocketType("Image");

let getSockets = () => {
    return [imgSocket];
}

//MONITOR DATA TYPES

export const IMG_DT = new MonitorDataType("IMAGE", "Image");
IMG_DT.registerDisplayMode(new MonitorDisplayMode(0, "Raw", DT_Image));
IMG_DT.registerDisplayMode(new MonitorDisplayMode(1, "Grayscale", DT_Image));
IMG_DT.registerDisplayMode(new MonitorDisplayMode(2, "Histogram", DT_Scatterplot, {
    "xtitle": "Intensity",
    "ytitle": "Count",
    "xrange": [0, 255],
    "xvisible": true,
    "yvisible": true,
    "plots": [{"line": {"color": "rgb(0, 0, 255)", "width": 1}},
        {"line": {"color": "rgb(0, 255, 0)", "width": 1}},
        {"line": {"color": "rgb(255, 0, 0)", "width": 1}}]}));

export const ARRAY_IMG_DT = new MonitorDataType("ARRAY_IMG", "Img Array");
ARRAY_IMG_DT.registerDisplayMode(new MonitorDisplayMode(0, "Count", DT_Literal));
ARRAY_IMG_DT.registerDisplayMode(new MonitorDisplayMode(1, "Delta", DT_Image));
ARRAY_IMG_DT.registerDisplayMode(new MonitorDisplayMode(2, "Sum", DT_Image));

let getDataTypes = () => {
    return [IMG_DT, ARRAY_IMG_DT];
}

// -------------------------------------------------------------------------

export default {Operators, Sources, getComponents, getSockets, getDataTypes}

export const Module = {
    name: "ImageProc",
    displayName: "Image Processing",
    bgColor: "radial-gradient(circle, rgb(131, 186, 255) 0%, rgb(94, 165, 255) 100%)"
}
