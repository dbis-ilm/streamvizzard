import Base from "@/scripts/pipeline/operators/modules/base";
import ImageProc from "@/scripts/pipeline/operators/modules/imageproc";
import DataCleaning from "@/scripts/pipeline/operators/modules/dataCleaning";
import SignalProc from "@/scripts/pipeline/operators/modules/signalProc";
import Examples from "@/scripts/pipeline/operators/modules/examples";

import {SocketType} from "@/scripts/pipeline/SvSocket";

const modules = [Base, DataCleaning, ImageProc, SignalProc];

// Exclude examples only if the env var explicitly states so
if(!(process.env.VUE_APP_INCLUDE_EXAMPLES === 'false')) modules.push(Examples)

export let getComponents = function() {
    let allComps = [];

    for(let m of modules) allComps = allComps.concat(m.getComponents());

    return allComps;
}

// ------------- SOCKETS -------------

export const anySocket = new SocketType("Any");

// ------------- MONITOR DATA TYPES -------------

let monitorDataTypes = {};

for(let m of modules) {
    for(let dt of m.getDataTypes()) {
        monitorDataTypes[dt.name] = dt;
    }
}

export let getDataTypeForName = function(name) {
    if(name == null) return null;

    let d = monitorDataTypes[name];
    if(d === undefined) return null;

    return d;
}
