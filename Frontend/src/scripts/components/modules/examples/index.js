import LaserWelding from "@/scripts/components/modules/examples/laserWelding";

let getComponents = () => {
    const ops =  LaserWelding.getComponents(["Laser Welding"]);

    for (const o in ops) {
        const path = ops[o].path;
        ops[o].path = [Module.name].concat(path);
        ops[o].contextPath = [Module.displayName].concat(path);
        ops[o].bgColor = Module.bgColor;
    }

    return ops;
}

//SOCKETS

let getSockets = () => {
    return [];
}

let getDataTypes = () => {
    return [];
}

// -------------------------------------------------------------------------

export default {
    LaserWelding, getSockets, getComponents, getDataTypes
}

export const Module = {
    name: "Examples",
    displayName: "Examples",
    bgColor: "radial-gradient(circle, rgb(255, 217, 136) 0%, rgb(255, 205, 100) 100%)"
}
