import HistoryAction from "@/scripts/tools/editorHistory/HistoryAction";
import {createNode} from "@/scripts/tools/Utils";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";

class NodeAction extends HistoryAction {
    constructor(editor, node) {
        super(editor);

        this.nodeID = node.id;
    }

    async createNode(data) {
        const component = this.editor.components.get(data.name);
        const node = await createNode(component,{"id": data.id, "x": data.x, "y": data.y});

        this.editor.addNode(node); // Triggers node created

        await DataExportService.loadOperatorFromSaveData(node, data.saveData); // This triggers operator data update
    }

    getNodeData(node) {
        return {"id": node.id, "name": node.name, "x": node.position[0], "y": node.position[1], "saveData": DataExportService.getOperatorSaveData(node)};
    }
}

export class AddNodeAction extends NodeAction {
    constructor(editor, node) {
        super(editor, node);

        this.createData = null;
    }

    async undo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        this.createData = this.getNodeData(node);
        this.editor.removeNode(node);
    }

    async redo() {
        await this.createNode(this.createData)
    }

    isPipelineChangeEvent() { return true; }
}

export class RemoveNodeAction extends NodeAction {
    constructor(editor, node) {
        super(editor, node);

        this.createData = this.getNodeData(node);
    }

    async undo() {
        await this.createNode(this.createData)
    }

    async redo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        this.editor.removeNode(node);
    }

    isPipelineChangeEvent() { return true; }
}

// Change Actions

export class NodeChangeAction extends NodeAction {
    constructor(editor, node) {
        super(editor, node);

        this.closed = false;

        this.prev = null;
        this.new = null;
    }
}

export class DragNodeAction extends NodeChangeAction {
    constructor(editor, node, prev) {
        super(editor, node);

        this.prev = [...prev];
        this.new = [...node.position];
    }

    isUIEvent() { return true; }

    async undo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        this.editor.view.nodes.get(node).translate(...this.prev);
        this.editor.trigger('nodedraged', node);
    }

    async redo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        this.editor.view.nodes.get(node).translate(...this.new);
        this.editor.trigger('nodedraged', node);
    }

    update(node) {
        this.new = [...node.position];
    }
}

//TODO: WHEN SOCKETS ARE REMOVED (UDF) AND UNDONE, CUSTOM SOCKET NAMES WILL BE LOST!
export class NodeParamChangeAction extends NodeChangeAction {
    constructor(editor, node, ctrlKey, prev) {
        super(editor, node);

        this.ctrlKey = ctrlKey;

        this.prev = prev;
        this.new = node.controls.get(ctrlKey).getValue();
    }

    async undo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        let ctrl = node.controls.get(this.ctrlKey);
        if(ctrl == null) return;

        ctrl.setValue(this.prev);
        node.component.onControlValueChanged(ctrl, node, this.new);  //To trigger changes in operator (pipelineState update)
    }

    async redo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        let ctrl = node.controls.get(this.ctrlKey);
        if(ctrl == null) return;

        ctrl.setValue(this.new);
        node.component.onControlValueChanged(ctrl, node, this.prev);  //To trigger changes in operator (pipelineState update)
    }

    update(node) {
        this.new = node.controls.get(this.ctrlKey).getValue();
    }

    isPipelineChangeEvent() { return true; }
}

export class NodeNameChangeAction extends NodeChangeAction {
    constructor(editor, node, prev) {
        super(editor, node);

        this.prev = prev;
        this.new = node.viewName;
    }

    isUIEvent() { return true; }

    async undo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        node.viewName = this.prev;
    }

    async redo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        node.viewName = this.new;
    }

    update(node) {
        this.new = node.viewName;
    }
}

export class NodeSocketNameChangeAction extends NodeChangeAction {
    constructor(editor, node, socket, prev) {
        super(editor, node);

        this.key = socket.key;
        this.prev = prev;
        this.new = socket.name;
    }

    isUIEvent() { return true; }

    async undo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        let socket = node.component.getSocketByKey(node, this.key);
        if(socket == null) return;

        socket.name = this.prev;

        await node.update();
    }

    async redo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if(node == null) return;

        let socket = node.component.getSocketByKey(node, this.key);
        if(socket == null) return;

        socket.name = this.new;

        await node.update();
    }

    update(socket) {
        this.new = socket.name;
    }
}

export class NodeResizeChangeAction extends NodeChangeAction {
    constructor(editor, node, prev) {
        super(editor, node);

        this.prev = prev;
        this.new = node.vueContext.getResizeData();
    }

    isUIEvent() { return true; }

    async undo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if (node == null) return;

        for(let r of this.prev) {
            node.vueContext.resizeElement(r.id, r.data.width, r.data.height);
        }

        this.editor.trigger("nodeResized", {"node": node, "prev": this.next});
    }

    async redo() {
        let node = PipelineService.getOperatorByID(this.nodeID);
        if (node == null) return;

        for(let r of this.new) {
            node.vueContext.resizeElement(r.id, r.data.width, r.data.height);
        }

        this.editor.trigger("nodeResized", {"node": node, "prev": this.prev});
    }

    update(node) {
        this.new = node.vueContext.getResizeData();
    }
}
