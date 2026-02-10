import {safeVal} from "@/scripts/tools/Utils";
import {SvInstance} from "@/scripts/StreamVizzard";

export function migrateSaveData(saveData) {
    try {
        let svVersion = safeVal(saveData["svVersion"]);

        if(svVersion === SvInstance.version) return saveData; // No migration required

        let compilerData = saveData["compiler"];

        let pipeline = safeVal(saveData["pipeline"]);
        if(pipeline == null) return null;

        let graph = safeVal(pipeline["graph"]);
        if(graph == null) return null;

        let ops = safeVal(pipeline["op"]);
        if(ops == null) return null;

        let opsData = {};
        let conData = [];

        for(let op of ops) opsData[op["id"]] = op;

        for(let [nodeID, nodeData] of Object.entries(safeVal(graph["nodes"], {}))) {
            let op = opsData[nodeID];
            if(op == null) continue;

            op["posX"] = nodeData["position"][0];
            op["posY"] = nodeData["position"][1];

            for(let [socketID, input] of Object.entries(nodeData["inputs"])) {
                for(let con of input["connections"]) {
                    conData.push({id: con["id"], inputOp: parseInt(nodeID), inputSocket: parseInt(socketID.replace("in", "")),
                        outputOp: parseInt(con["node"]), outputSocket: parseInt(con["output"].replace("out", ""))});
                }
            }

            for(let [socketID, output] of Object.entries(nodeData["outputs"])) {
                for(let con of output["connections"]) {
                    conData.push({id: con["id"], inputOp: parseInt(con["node"]), inputSocket: parseInt(con["input"].replace("in", "")),
                        outputOp: parseInt(nodeID), outputSocket: parseInt(socketID.replace("out", ""))});
                }
            }

            if(compilerData != null) {
                let compOpData = compilerData["configs"]?.[nodeID];
                if(compOpData != null) op["compiler"] = {"config": compOpData};
            }
        }

        pipeline["operators"] = Object.values(opsData);
        pipeline["connections"] = conData;

        if(compilerData != null) {
            pipeline["compiler"] = {
                "placementSettings": compilerData["placementSettings"],
                "compileSettings": compilerData["compileSettings"]
            };
        }

        return saveData;
    } catch (error) {
        console.error("Failed to migrate save data with error:", error);

        return null;
    }
}

export function migrateOperatorSaveData(opData) {
    try {
        let svVersion = safeVal(opData["svVersion"]);

        if(svVersion === SvInstance.version) return opData; // No migration required

        opData["params"] = opData["data"];
        opData["name"] = opData["dName"];
        opData["definition"] = opData["path"].replace("E4SM", "Laser Welding");

        // Omitted non-functional migrations

        return opData;
    } catch (error) {
        console.error("Failed to migrate operator save data with error:", error);

        return null;
    }
}