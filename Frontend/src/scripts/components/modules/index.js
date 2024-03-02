import Base from "@/scripts/components/modules/base";
import ImageProc from "@/scripts/components/modules/imageproc";
import Rete from "rete";

const modules = [Base, ImageProc];

let getComponents = function() {
    let allComps = [];

    for(let m of modules) allComps = allComps.concat(m.getComponents());

    return allComps;
}

// ------------- SOCKETS -------------

export const anySocket = new Rete.Socket('Any');

for(let m of modules) {
    for (let s of m.getSockets()) {
        anySocket.combineWith(s);
        s.combineWith(anySocket);
    }
}

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

export default {
    Base, ImageProc, getComponents
}
