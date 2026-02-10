import HistoryAction from "@/scripts/tools/editorHistory/HistoryAction";
import {SvInstance} from "@/scripts/StreamVizzard";
import {safeVal} from "@/scripts/tools/Utils";

class OperatorAction extends HistoryAction {
    /** @param {SvOperator} op **/
    constructor(op) {
        super();

        this.opID = op.id;

        this.saveData = null;
    }

    deleteOperator() {
        let op = SvInstance.pipeline.getOperatorByID(this.opID);
        if(op == null) return false;

        this.saveData = op.exportSaveData();

        return SvInstance.pipeline.deleteOperator(op);
    }

    async createOperator() {
        return await SvInstance.pipeline.createOperatorFromSaveData(this.saveData) != null;
    }
}

export class AddOperatorAction extends OperatorAction {
    async undo() {
        return this.deleteOperator();
    }

    async redo() {
        return await this.createOperator();
    }

    isPipelineChangeEvent() { return true; }
}

export class RemoveOperatorAction extends OperatorAction {
    /** @param {SvOperator} op **/
    constructor(op) {
        super(op);

        this.saveData = op.exportSaveData();
    }

    async undo() {
        return await this.createOperator();
    }

    async redo() {
        return this.deleteOperator();
    }

    isPipelineChangeEvent() { return true; }
}

//Care: When sockets are removed (UDF) AND UNDONE, CUSTOM SOCKET NAMES WILL BE LOST!
export class OperatorParamCA extends OperatorAction {
    /** @param {SvOperator} op
     *  @param {Param} param
     *  @param {any} prev **/
    constructor(op, param, prev) {
        super(op);

        this.key = param.key;

        this.prev = prev;
        this.new = param.getValue();
    }

    setParam(newData) {
        let op = SvInstance.pipeline.getOperatorByID(this.opID);
        if(op == null) return false;

        let param = op.getParam(this.key);
        if(param == null) return false;

        let currentVal = param.getValue();

        param.setValue(newData);

        return currentVal !== param.getValue();
    }

    async undo() {
        return this.setParam(this.prev);
    }

    async redo() {
        return this.setParam(this.new);
    }

    isPipelineChangeEvent() { return true; }
}

export class OperatorNameCA extends OperatorAction {
    /** @param {SvOperator} op
     *  @param {String} prev **/
    constructor(op, prev) {
        super(op);

        this.prev = prev;
        this.new = op.name;
    }

    isUIEvent() { return true; }

    setName(newName) {
        let op = SvInstance.pipeline.getOperatorByID(this.opID);
        if(op == null) return false;

        let currentName = op.name;

        op.name = newName;

        return op.name !== currentName;
    }

    async undo() {
        return this.setName(this.prev);
    }

    async redo() {
        return this.setName(this.new);
    }
}

export class SocketNameCA extends OperatorAction {
    /** @param {SvOperator} op
     *  @param {SvSocket} socket
     *  @param {String} prev **/
    constructor(op, socket, prev) {
        super(op);

        this.socketID = socket.id;
        this.inputSocket = socket.input;
        this.prev = prev;
        this.new = socket.name;
    }

    isUIEvent() { return true; }

    setName(newName) {
        let op = SvInstance.pipeline.getOperatorByID(this.opID);
        if(op == null) return false;

        let socket = op.getSocketByID(this.socketID, this.inputSocket);
        if(socket == null) return false;

        let currentName = socket.name;

        socket.name = newName;

        return socket.name !== currentName;
    }

    async undo() {
        return this.setName(this.prev);
    }

    async redo() {
        return this.setName(this.new);
    }
}

// Change Actions

export class OperatorChangeAction extends OperatorAction {
    /** @param {SvOperator} op **/
    constructor(op) {
        super(op);

        this.prev = null;
        this.new = null;
    }
}

export class DragOperatorCA extends OperatorChangeAction {
    /** @param {SvOperator} op
     * @param {Object} prev **/
    constructor(op, prev) {
        super(op);

        this.prev = [prev.x, prev.y];
        this.new = [op.posX, op.posY];
    }

    isUIEvent() { return true; }

    setPos(newX, newY) {
        let op = SvInstance.pipeline.getOperatorByID(this.opID);
        if(op == null) return false;

        let prevX = op.posX;
        let prevY = op.posY;

        op.moveTo(newX, newY); // No need to trigger drag since groups will receive their own events (memberships)

        return op.posX !== prevX || op.posY !== prevY;
    }

    async undo() {
        return this.setPos(this.prev[0], this.prev[1]);
    }

    async redo() {
        return this.setPos(this.new[0], this.new[1]);
    }

    /** @param {SvOperator} op **/
    update(op) {
        this.new = [op.posX, op.posY];
    }
}

export class OperatorResizeCA extends OperatorChangeAction {
    /** @param {SvOperator} op
     *  @param {any} prev **/
    constructor(op, prev) {
        super(op);

        this.prev = prev;
        this.new = op.getResizeData();
    }

    isUIEvent() { return true; }

    resizeOp(resizeData) {
        let op = SvInstance.pipeline.getOperatorByID(this.opID);
        if (op == null) return false;

        for(let rd of safeVal(resizeData["entries"], []))
            op.resizeElement(rd["id"], resizeData["width"], rd["height"]);

        return true;
    }

    async undo() {
        return this.resizeOp(this.prev);
    }

    async redo() {
        return this.resizeOp(this.new);
    }

    /** @param {SvOperator} op **/
    update(op) {
        this.new = op.getResizeData();
    }
}
