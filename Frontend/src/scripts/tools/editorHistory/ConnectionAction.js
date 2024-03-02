import HistoryAction from "@/scripts/tools/editorHistory/HistoryAction";
import {getOperatorByID} from "@/components/Main";

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
        let outNode = getOperatorByID(this.outNodeID);
        if(outNode == null) return;

        let connection = outNode.outputs.get(this.outSocketKey).connections
            .find(c => c.input.node.id === this.inNodeID && c.input.key === this.inSocketKey);

        this.lastTotal = connection.total;
        this.lastTP = connection.throughput;

        this.editor.removeConnection(connection);
    }

    createConnection() {
        let nodeOut = getOperatorByID(this.outNodeID);
        if(nodeOut == null) return;

        let nodeIn = getOperatorByID(this.inNodeID); //NULL when recreating deleted op
        if(nodeIn == null) return;

        let socketOut = nodeOut.outputs.get(this.outSocketKey);
        let socketIn = nodeIn.inputs.get(this.inSocketKey);

        this._connect(socketOut, socketIn, this.connectionID);

        //Update stats
        let connection = socketOut.connections.find(c => c.input.node.id === this.inNodeID && c.input.key === this.inSocketKey);
        connection.total = this.lastTotal;
        connection.throughput = this.lastTP;
    }

    _connect(output, input, id) {
        //Override connect to set id before calling the events
        if (!this.editor.trigger('connectioncreate', { output, input })) return;

        try {
            const connection = output.connectTo(input);

            connection.id = id;
            this.editor.view.addConnection(connection);

            this.editor.trigger('connectioncreated', connection);
        } catch (e) {
            this.editor.trigger('warn', e);
        }
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
