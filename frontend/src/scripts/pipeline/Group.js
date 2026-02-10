import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import {SvInstance} from "@/scripts/StreamVizzard";
import {getOperatorBoundingBox} from "@/scripts/tools/Utils";
import TemplateHost from "@/scripts/tools/TemplateHost";

export class Group extends TemplateHost {
    /** @type String */ title = "Group";
    /** @type Number */ id;

    /** @type Number */ x;
    /** @type Number */ y;

    /** @type {Object<number, SvOperator>} */ operators = {};
    /** @type GroupCache */ cache = new GroupCache(this);

    // Calculated

    /** @type Number */ width;
    /** @type Number */ height;

    /** @type Boolean */ nodeAddHover;
    /** @type Number */ order; // For bringing group to front

    constructor(id) {
        super();

        this.id = id;
    }

    /** @param {SvOperator} operator **/
    addOperator(operator) {
        if(operator.group != null) return false; // Each op can only have one group

        this.operators[operator.id] = operator;
        operator.group = this;

        this.updateTransform();

        executeEvent(EVENTS.GROUP_OP_ADDED, [this, operator]);

        return true;
    }

    /** @param {SvOperator} operator
     * @param {boolean} updateTransform **/
    removeOperator(operator, updateTransform=true) {
        if(operator.group !== this) return false;

        delete this.operators[operator.id];

        operator.group = null;

        executeEvent(EVENTS.GROUP_OP_REMOVED, [this, operator]);

        if(Object.keys(this.operators).length === 0) {
            SvInstance.pipeline.deleteGroup(this);

            return true;
        }

        if(updateTransform) this.updateTransform();

        return true;
    }

    remove() {
        for(let op of Object.values(this.operators))
            this.removeOperator(op, false);
    }

    selectGroup() {
        // Promote all operators (in their current ASC order) of this group to bring them to the front above other ops

        let sortedOps = Object.values(this.operators).slice().sort((a, b) => a.order - b.order);

        for(let op of sortedOps) op.promoteOrder();

        // Group order is the lowest order of the included ops

        this.order = sortedOps[0].order;

        // Also promote all connections that are part of this group (both sockets must belong to op of group)

        for(let op of sortedOps) {
            for(let con of op.getAllConnections()) {
                if(con.input.operator.group !== this || con.output.operator.group !== this) continue;

                con.order = this.order;
            }
        }
    }

    unselectGroup() {
        this.order = null;

        for(let op of Object.values(this.operators)) {
            for(let con of op.getAllConnections()) con.order = null;
        }
    }

    moveGroup(newX, newY) {
        let oldX = this.x;
        let oldY = this.y;

        if(oldX === newX && oldY === newY) return false;

        let dX = newX - oldX;
        let dY = newY - oldY;

        let containedReroutes = this.cache.requestContainedReroutes(); // Calc before group is moved

        this.x = newX;
        this.y = newY;

        executeEvent(EVENTS.GROUP_MOVED, [this, {x: oldX, y: oldY}]); // Call before ops are translated!

        for(let op of Object.values(this.operators)) op.moveTo(op.posX + dX, op.posY + dY, true);

        for(let rr of containedReroutes) rr.con.updateReroutePin(rr, rr.x + dX, rr.y + dY, true);

        return true;
    }

    updateTransform() {
        const { left, top, width, height } = getOperatorBoundingBox(Object.values(this.operators), 20);

        this.x = left;
        this.y = top;
        this.width = width;
        this.height = height;
    }

    /** @param {SvOperator} op **/
    intersectsOp(op) {
        let left = this.x;
        let right = this.x + this.width;
        let top = this.y;
        let bottom = this.y + this.height;

        let opLeft = op.posX;
        let opRight = opLeft + op.width;
        let opTop = op.posY;
        let opBottom = opTop + op.height;

        return !(
            opLeft > right ||
            opRight < left ||
            opTop > bottom ||
            opBottom < top
        );
    }

    /** @param {Number} x
     * @param {Number} y */
    containsPoint(x, y) {
        return (
            x >= this.x &&
            x <= this.x + this.width &&
            y >= this.y &&
            y <= this.y + this.height
        );
    }

    // ------------------------------------------------ Config / Storage -----------------------------------------------

    exportSaveData() {
        return {"id": this.id, "title": this.title,
            "operators": Object.keys(this.operators).map(k => parseInt(k))};
    }
}

/** Stores information to speed up calculation during drag operations */
class GroupCache {
    /** @param {Group} group */
    constructor(group) {
        this.group = group;

        /** @type {Array<ReroutePin>|null} */
        this._containedReroutes = null;
    }

    /** @returns {Array<ReroutePin>} */
    requestContainedReroutes() {
        if(this._containedReroutes != null) return this._containedReroutes;

        let containedReroutes = [];

        let conLookup = {};

        for(let op of Object.values(this.group.operators)) {
            for(let con of op.getAllConnections()) {
                if(con.id in conLookup) continue; // Don't handle connections twice (in case inter-group-cons)
                conLookup[con.id] = true;

                for(let pin of con.reroutes) {
                    if(this.group.containsPoint(pin.x, pin.y)) containedReroutes.push(pin);
                }
            }
        }

        return containedReroutes;
    }

    update() {
        this._containedReroutes = this.requestContainedReroutes();
    }

    clear() {
        this._containedReroutes = null;
    }
}
