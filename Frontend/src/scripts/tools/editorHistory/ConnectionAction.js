import HistoryAction from "@/scripts/tools/editorHistory/HistoryAction";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";
import {createConnection} from "@/scripts/tools/Utils";

class ConnectionAction extends HistoryAction {
    constructor(editor, con) {
        super(editor);

        this.outNodeID = con.output.node.id;
        this.inNodeID = con.input.node.id;
        this.outSocketKey = con.output.key;
        this.inSocketKey = con.input.key;

        this.lastTP = con.throughput;
        this.lastTotal = con.total;

        this.connectionID = con.id;
    }

    removeConnection() {
        let outNode = PipelineService.getOperatorByID(this.outNodeID);
        if(outNode == null) return;

        let connection = outNode.outputs.get(this.outSocketKey).connections
            .find(c => c.input.node.id === this.inNodeID && c.input.key === this.inSocketKey);

        this.lastTotal = connection.total;
        this.lastTP = connection.throughput;

        this.editor.removeConnection(connection);
    }

    createConnection() {
        let nodeOut = PipelineService.getOperatorByID(this.outNodeID);
        if(nodeOut == null) return;

        let nodeIn = PipelineService.getOperatorByID(this.inNodeID); //NULL when recreating deleted op
        if(nodeIn == null) return;

        let socketOut = nodeOut.outputs.get(this.outSocketKey);
        let socketIn = nodeIn.inputs.get(this.inSocketKey);

        createConnection(this.editor, socketOut, socketIn, this.connectionID);

        // Update stats
        let connection = socketOut.connections.find(c => c.input.node.id === this.inNodeID && c.input.key === this.inSocketKey);
        connection.total = this.lastTotal;
        connection.throughput = this.lastTP;
    }

    isPipelineChangeEvent() { return true; }
}

export class AddConnectionAction extends ConnectionAction {
    async undo() {
        this.removeConnection();
    }

    async redo() {
        this.createConnection();
    }
}

export class RemoveConnectionAction extends ConnectionAction {
    async undo() {
        this.createConnection();
    }

    async redo() {
        this.removeConnection();
    }
}
