import Operators from "@/scripts/components/modules/dataCleaning/operators";

let getComponents = () => {
    const ops =  Operators.getComponents(["Operators"])

    for (const o in ops) {
        const path = ops[o].path;
        ops[o].path = [Module.name].concat(path);
        ops[o].contextPath = [Module.displayName].concat(path);
        ops[o].bgColor = Module.bgColor;
    }

    return ops;
}

let getDataTypes = () => {
    return [];
}

//SOCKETS

let getSockets = () => {
    return [];
}

// -------------------------------------------------------------------------

export default {
    Operators, getComponents, getSockets, getDataTypes
}

export const Module = {
    name: "DataCleaning",
    displayName: "Data Cleaning",
    bgColor: "radial-gradient(circle, rgb(212, 142, 255) 0%, rgb(201, 109, 255) 100%)"
}
