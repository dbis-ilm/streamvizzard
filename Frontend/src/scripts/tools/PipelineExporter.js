import {operatorLookup, registerDataExporter} from "@/components/Main";
import {system} from "@/main";
import {getOperatorSaveData, loadOperatorFromSaveData} from "@/scripts/tools/Utils";

export function initializePipelineExporter() {
    registerDataExporter("pipeline", savePipeline, loadPipeline);
}

function savePipeline() {
    //Basic structure of graph
    let graph = system.editor.toJSON();

    //Store parameters and names of links/operators that are not included yet in the graph
    let opData = [];

    for(let [, op] of operatorLookup) opData.push(getOperatorSaveData(op));

    return {"graph": graph, "op": opData};
}

async function loadPipeline(data) {
    let graphData = data.graph;
    let graphDataOperatorsOnly = JSON.parse(JSON.stringify(graphData)); //Clone object

    //Clear Connection Data from Operators because this will be handled after parameter data was applied

    for(let id in graphDataOperatorsOnly.nodes) {
        let op = graphDataOperatorsOnly.nodes[id];

        for(let inputID in op.inputs) {
            op.inputs[inputID].connections = [];
        }

        for(let outputID in op.outputs) {
            op.outputs[outputID].connections = [];
        }
    }

    //Load Operators and Positions

    await system.editor.fromJSON(graphDataOperatorsOnly);

    //Apply operator parameters and custom display names

    for(let d of data.op) {
        let operator = operatorLookup.get(d.id);

        await loadOperatorFromSaveData(operator, d);
    }

    //Apply connections between all operators

    for(let id in graphData.nodes) {
        let op = graphData.nodes[id];
        let operator = operatorLookup.get(op.id);

        operator.component.clearAllConnections(operator);

        for(let inputID in op.inputs) {
            for(let con of op.inputs[inputID].connections) {
                let otherOp = operatorLookup.get(con.node);

                system.editor.connect(otherOp.outputs.get(con.output), operator.inputs.get(inputID));
            }
        }

        for(let outputID in op.outputs) {
            for(let con of op.outputs[outputID].connections) {
                let otherOp = operatorLookup.get(con.node);

                system.editor.connect(operator.outputs.get(outputID), otherOp.inputs.get(con.input));
            }
        }
    }
}
