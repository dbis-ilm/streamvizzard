import Operators from "@/scripts/components/modules/imageproc/operators";
import Sources from "@/scripts/components/modules/imageproc/sources";
import Rete from "rete";
import Scatterplot from "@/components/templates/displays/ScatterplotDT";
import {MonitorDataType} from "@/scripts/components/monitor/MonitorDataType";
import ImageDT from "@/components/templates/displays/ImageDT";
import LiteralDT from "@/components/templates/displays/LiteralDT";


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

export const imgSocket = new Rete.Socket('Image');

let getSockets = () => {
    return [imgSocket];
}

//MONITOR DATA TYPES

export const IMG_DT = new MonitorDataType("IMAGE", "Image");
IMG_DT.registerDisplayMode(0, "Raw", ImageDT);
IMG_DT.registerDisplayMode(1, "Grayscale", ImageDT);
IMG_DT.registerDisplayMode(2, "Histogram", Scatterplot, {
    "xrange": [0, 255],
    xvisible: true,
    yvisible: false,
    "plots": [{"line": {"color": "rgb(0, 0, 255)", "width": 1}},
        {"line": {"color": "rgb(0, 255, 0)", "width": 1}},
        {"line": {"color": "rgb(255, 0, 0)", "width": 1}}]});

export const ARRAY_IMG_DT = new MonitorDataType("ARRAY_IMG", "Img Array");
ARRAY_IMG_DT.registerDisplayMode(0, "Count", LiteralDT);
ARRAY_IMG_DT.registerDisplayMode(1, "Delta", ImageDT);
ARRAY_IMG_DT.registerDisplayMode(2, "Sum", ImageDT);

let getDataTypes = () => {
    return [IMG_DT, ARRAY_IMG_DT];
}

// -------------------------------------------------------------------------

export default {Operators, Sources, getComponents, getSockets, getDataTypes}

export const Module = {
    name: "ImageProc",
    displayName: "Images",
    bgColor: "radial-gradient(circle, rgba(94, 165, 255,0.75) 0%, rgba(94, 165, 255,0.9) 100%)"
}
