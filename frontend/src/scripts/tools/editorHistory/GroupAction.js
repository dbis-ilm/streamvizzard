import HistoryAction from "@/scripts/tools/editorHistory/HistoryAction";
import {SvInstance} from "@/scripts/StreamVizzard";

class GroupAction extends HistoryAction {
    /** @param {Group} group **/
    constructor(group) {
        super();

        this.groupID = group.id;
        this.prevGroupData = group.exportSaveData();
    }

    isUIEvent() { return true; }

    addOperator(opID) {
        let op = SvInstance.pipeline.getOperatorByID(opID);
        if(op == null) return false;

        // If op was last op, group was removed -> need to restore first
        if(this.getGroup() == null) SvInstance.pipeline.createGroupFromSaveData(this.prevGroupData, true);

        return this.getGroup().addOperator(op);
    }

    removeOperator(opID) {
        let op = SvInstance.pipeline.getOperatorByID(opID);
        if(op == null) return false;

        return this.getGroup().removeOperator(op); // Might remove group if its last op
    }

    getGroup() {
        return SvInstance.pipeline.getGroupById(this.groupID);
    }
}

export class GroupOperatorAdded extends GroupAction {
    /** @param {Group} group
     *  @param {SvOperator} op **/
    constructor(group, op) {
        super(group);

        this.opID = op.id;
    }

    async undo() {
        return this.removeOperator(this.opID);
    }

    async redo() {
        return this.addOperator(this.opID);
    }
}

export class GroupOperatorRemoved extends GroupAction {
    /** @param {Group} group
     *  @param {SvOperator} op **/
    constructor(group, op) {
        super(group);

        this.opID = op.id;
    }

    async undo() {
        return this.addOperator(this.opID);
    }

    async redo() {
        return this.removeOperator(this.opID);
    }
}

export class GroupNameChangeAction extends GroupAction {
    /** @param {Group} group
     * @param {string} prev **/
    constructor(group, prev) {
        super(group);

        this.prev = prev;
        this.new = group.title;
    }

    async undo() {
        let group = this.getGroup();
        let currentTitle = group.title;

        group.title = this.prev;

        return group.title !== currentTitle;
    }

    async redo() {
        let group = this.getGroup();
        let currentTitle = group.title;

        group.title = this.new;

        return group.title !== currentTitle;
    }
}

// Change Actions

export class GroupChangeAction extends GroupAction {
    /** @param {Group} group **/
    constructor(group) {
        super(group);

        this.prev = null;
        this.new = null;
    }
}

// Future Work: When reverting a group move, reroute pins might be not "released" from the group and moved as well
// since groups don't track which pins belong to them and solely determine them by bounding box calculations.

export class GroupMoveAction extends GroupChangeAction {
    /** @param {Group} group
     * @param {Object} prev **/
    constructor(group, prev) {
        super(group);

        this.prev = [prev.x, prev.y];
        this.new = [group.x, group.y];
    }

    async undo() {
        return this.getGroup().moveGroup(this.prev[0], this.prev[1]);
    }

    async redo() {
        return this.getGroup().moveGroup(this.new[0], this.new[1]);
    }

    update() {
        let group = this.getGroup();

        this.new = [group.x, group.y];
    }
}
