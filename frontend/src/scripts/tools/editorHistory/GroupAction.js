import HistoryAction from "@/scripts/tools/editorHistory/HistoryAction";
import {globalCommentManager} from "@/plugins/rete-comment-plugin";

class GroupAction extends HistoryAction {
    constructor(editor, group) {
        super(editor);

        this.groupID = group.getID();

        this.removedGroup = group; //For tracking the old group data to restore
    }

    isUIEvent() { return true; }

    createGroup() {
        let group = this.removedGroup;

        let newGroup = globalCommentManager.addFrameComment(group.text, [group.x, group.y],
            group.links, group.width, group.height, group.collapsed, false);
        newGroup.updateID(this.groupID);
    }

    removeGroup() {
        let group = this.getGroup();
        this.removedGroup = group;

        this.links = group.links;
        this.editor.trigger('removecomment', {comment: group});
    }

    getGroup() {
        return globalCommentManager.getComment(this.groupID);
    }
}

export class AddGroupAction extends GroupAction {
    constructor(editor, group) {
        super(editor, group);
    }

    async undo() {
        this.removeGroup();
    }

    async redo() {
        this.createGroup(this.group);
    }
}

export class RemoveGroupAction extends GroupAction {
    constructor(editor, group) {
        super(editor, group);
    }

    async undo() {
        this.createGroup();
    }

    async redo() {
        this.removeGroup();
    }
}

export class CollapseGroupAction extends GroupAction {
    constructor(editor, group, collapse) {
        super(editor, group);

        this.collapsed = collapse;
    }

    async undo() {
        this.getGroup().instance.setCollapsed(!this.collapsed, true);
    }

    async redo() {
        this.getGroup().instance.setCollapsed(this.collapsed, true);
    }
}

// Change Actions

export class GroupChangeAction extends GroupAction {
    constructor(editor, group) {
        super(editor, group);

        this.closed = false;

        this.prev = null;
        this.new = null;
    }
}

export class DragGroupAction extends GroupChangeAction {
    constructor(editor, group, prev) {
        super(editor, group);

        this.prev = prev;
        this.new = [group.x, group.y];
    }

    async undo() {
        this.getGroup().translate(this.prev[0], this.prev[1]);
    }

    async redo() {
        this.getGroup().translate(this.new[0], this.new[1]);
    }

    update() {
        let group = this.getGroup();

        this.new = [group.x, group.y];
    }
}

export class GroupNameChangeAction extends GroupChangeAction {
    constructor(editor, group, prev) {
        super(editor, group);

        this.prev = prev;
        this.new = group.text;
    }

    async undo() {
        this.getGroup().text = this.prev;
    }

    async redo() {
        this.getGroup().text = this.new;
    }

    update(group) {
        this.new = group.text;
    }
}

export class GroupSizeChangeAction extends GroupChangeAction {
    constructor(editor, group, prev) {
        super(editor, group);

        this.prev = prev;
        this.new = [group.width, group.height];
    }

    async undo() {
        let group = this.getGroup();

        group.updateSize(this.prev[0], this.prev[1]);
        group.afterSizeChangedFinished();
    }

    async redo() {
        let group = this.getGroup();

        group.updateSize(this.new[0], this.new[1]);
        group.afterSizeChangedFinished();
    }

    update(group) {
        this.new = [group.width, group.height];
    }
}
