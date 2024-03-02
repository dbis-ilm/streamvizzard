import Comment from './comment';
import { containsRect } from './utils';
import {operatorLookup} from "@/components/Main";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";

export default class FrameComment extends Comment {
    constructor(text, editor) {
        super(text, editor);

        this.width = 0;
        this.height = 0;
        this.links = [];
        this.collapsed = false;
    }

    linkedNodesView() {
        return this.links
            .map(id => this.editor.nodes.find(n => n.id === id))
            .map(node => this.editor.view.nodes.get(node));
    }

    onStart() {
        super.onStart();
        this.linkedNodesView().map(nodeView => nodeView.onStart())
    }

    translate(x, y) {
        let oldX = this.x;
        let oldY = this.y;

        super.translate(x, y);

        // Translate nodes relative to group
        this.linkedNodesView().map(nodeView => {
            let dx = nodeView.node.position[0] - oldX;
            let dy = nodeView.node.position[1] - oldY;
            nodeView.translate(x + dx, y + dy);
        });
    }

    onTranslate(dx, dy) { //For dragging
        super.onTranslate(dx, dy);
        this.linkedNodesView().map(nodeView => nodeView.onDrag(dx, dy))
    }

    isContains(node) {
        const commRect = this.el.getBoundingClientRect();
        const view = this.editor.view.nodes.get(node);

        return containsRect(commRect, view.el.getBoundingClientRect());
    }

    collapse(triggerNode) {
        if(triggerNode) {
            for(let link of this.links) {
                if(operatorLookup.has(link)) {
                    let node = operatorLookup.get(link);
                    node.component.setDataMonitorState(node, false, false);
                }
            }
        }

        this.collapsed = true;
        //Handled by nodeMonitorStateChanged event

        //Update size to fit nodes
        if(triggerNode) this.editor.trigger("syncframe", this);
    }

    expand(triggerNode) {
        if(triggerNode) {
            for(let link of this.links) {
                if(operatorLookup.has(link)) {
                    let node = operatorLookup.get(link);
                    node.component.setDataMonitorState(node, true, false);
                }
            }
        }

        this.collapsed = false;
        //Handled by nodeMonitorStateChanged event

        //Update size to fit nodes
        if(triggerNode) this.editor.trigger("syncframe", this);
    }

    update() {
        super.update();

        this.el.style.width = this.width+'px';
        this.el.style.height = this.height+'px';
    }

    updateSize(newWidth, newHeight) {
        let old = [this.width, this.height];

        this.width = newWidth;
        this.height = newHeight

        this.update();

        executeEvent(EVENTS.GROUP_SIZE_CHANGED, [this, old]);
    }

    afterSizeChangedFinished() {
        // Remove left/top positions and apply it to the coordinates
        let sx = parseFloat(this.el.style.left.replace("px", ""));
        let sy = parseFloat(this.el.style.top.replace("px", ""));

        if(!isNaN(sx)) this.x += sx;
        if(!isNaN(sy)) this.y += sy;

        //Remove position due to resize
        this.el.style.left = "unset";
        this.el.style.top = "unset";

        this.update();

        //Check all nodes if they are now inside the group
        let newLinks = [];
        for(let node of this.editor.nodes) {
            if(this.isContains(node))
                newLinks.push(node.id);
        }

        this.links = newLinks;
    }

    toJSON() {
        return {
            ...super.toJSON(),
            type: 'frame',
            width: this.width,
            height: this.height,
            collapsed: this.collapsed
        }
    }
}
