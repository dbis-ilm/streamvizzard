import {SvInstance} from "@/scripts/StreamVizzard";

/** @return {SvOperator} **/
function getOtherClusterSideCompileOp(opID, conID) {
    let con = SvInstance.pipeline.getConnectionByID(conID);

    return con.input.operator.id === opID ? con.output.operator : con.input.operator;
}

export function matchOtherClusterSideParams(opID, conID, paramKey, paramValue) {
    // Fetches operator of other side of the connection and sets matching
    // params of his selected connector to our changed value.

    let otherClusterOp = getOtherClusterSideCompileOp(opID, conID);
    if(otherClusterOp == null) return;

    if(otherClusterOp.compiler.specs == null || otherClusterOp.compiler.config == null) return;

    // Gets the config for the connector of the current connection

    if(otherClusterOp.compiler.config.cluster == null) return;

    let otherCon = otherClusterOp.compiler.config.cluster.ccs[conID];
    if(otherCon == null) return;

    // Adapt params, only consider params of his selected connector - full path for safe store into node data

    otherClusterOp.compiler.config.cluster.ccs[conID].params = matchParams({[paramKey]: paramValue}, otherCon.params);
}

export function matchOtherClusterSideConType(opID, conID, conType, conParams) {
    // Adapt other side of the cluster to select a matching connector to ours [if possible]

    let otherClusterOp = getOtherClusterSideCompileOp(opID, conID);
    if(otherClusterOp == null) return false;

    if(otherClusterOp.compiler.specs == null || otherClusterOp.compiler.config == null) return false;

    let otherClusterOptions = otherClusterOp.compiler.specs.clusterConOptions[conID] ?? null

    // Gets the config for the connector of the current connection

    if(otherClusterOptions == null && otherClusterOp.compiler.config.cluster == null) return false;

    let otherClusterCfg = otherClusterOp.compiler.config.cluster.ccs[conID];
    if(otherClusterCfg == null) return false;

    // Choose connector that has our value for "otherConType"

    for(let option of otherClusterOptions) {
        if(option.otherConType === conType) {
            otherClusterCfg.conType = option.ourConType;
            otherClusterCfg.params = {...option.ourConParams};

            // Match other keys with ours - full path for safe store into node data

            otherClusterOp.compiler.config.cluster.ccs[conID].params = matchParams(conParams, otherClusterCfg.params);

            return true;
        }
    }

    return false;
}

function matchParams(ourParams, otherParams) {
    for(let [paramKey, paramValue] of Object.entries(ourParams)) {
        for(let ok of Object.keys(otherParams)) {
            if(ok === paramKey) otherParams[ok] = paramValue;
        }
    }

    return otherParams;
}
