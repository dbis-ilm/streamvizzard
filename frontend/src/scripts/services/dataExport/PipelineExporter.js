import {system} from "@/main";
import {PipelineMetaData} from "@/scripts/services/pipelineState/PipelineMetaData";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";
import {createConnection} from "@/scripts/tools/Utils";

export function initializePipelineExporter() {
    DataExportService.registerDataExporter("pipeline", savePipeline, loadPipeline);
}

function savePipeline() {
    //Basic structure of graph
    let graph = system.editor.toJSON();

    // Add connection ids to the graph

    for(let node of Object.values(graph.nodes)) {
        delete node["data"]; // Remove data entry which we add in our own op entries

        for(let [socketKey, input] of Object.entries(node.inputs)) {
            for(let con of input.connections) {
                let conEl = PipelineService.getConnectionBetween(node.id, con.node, socketKey, con.output);

                if(conEl != null) con["id"] = conEl.id;
            }
        }

        for(let [socketKey, output] of Object.entries(node.outputs)) {
            for(let con of output.connections) {
                let conEl = PipelineService.getConnectionBetween(con.node, node.id, con.input, socketKey);

                if(conEl != null) con["id"] = conEl.id;
            }
        }
    }

    //Store parameters and names of links/operators that are not included yet in the graph
    let opData = [];

    for(let op of PipelineService.getAllOperators()) opData.push(DataExportService.getOperatorSaveData(op));

    return {"graph": graph, "op": opData, "meta": PipelineService.pipelineMetaData};
}

async function loadPipeline(data) {
    let graphData = data.graph;
    graphData["id"] = DataExportService.getEditorVersionID(); // For backwards compatibility of old saveFiles

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
        let operator = PipelineService.getOperatorByID(d.id);
        if(operator == null) continue;

        await DataExportService.loadOperatorFromSaveData(operator, d);

        operator.component.clearAllConnections(operator);
    }

    //Apply connections between all operators (only need to consider inputs since each input is connected to an output)

    for(let id in graphData.nodes) {
        let op = graphData.nodes[id];

        let operator = PipelineService.getOperatorByID(op.id);
        if(operator == null) continue;

        for(let inputID in op.inputs) {
            for(let con of op.inputs[inputID].connections) {
                let otherOp = PipelineService.getOperatorByID(con.node);
                if(otherOp == null) continue;

                createConnection(system.editor, otherOp.outputs.get(con.output), operator.inputs.get(inputID), con.id);
            }
        }
    }

    if("meta" in data) PipelineService.pipelineMetaData = Object.assign(new PipelineMetaData(), data["meta"]);
}
