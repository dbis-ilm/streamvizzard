import {SvInstance} from "@/scripts/StreamVizzard";
import HistoryAction from "@/scripts/tools/editorHistory/HistoryAction";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";
import {ReroutePin} from "@/scripts/pipeline/SvConnection";

/** Captures the movement event of all draggable objects (operators, pins).
 * Groups are isolated since currently they can not be moved together with other elms. **/
export class MoveAction extends HistoryAction {
    /** @param {SvOperator | ReroutePin} elm
     * @param {Object} prev **/
    constructor(elm, prev) {
        super();

        // Captures multiple op/reroute movement changes
        this.involvedOps = new Map();
        this.involvedCons = new Map();

        // Initial entry that created this event
        this.addEntry(elm, prev);
    }

    /** @param {SvOperator | ReroutePin} elm
     * @param {Object} prev **/
    addEntry(elm, prev) {
        if(elm instanceof SvOperator) this.involvedOps.set(elm.id, {prev: [prev.x, prev.y], new: [elm.posX, elm.posY]});
        else if(elm instanceof ReroutePin) this.involvedCons.set(elm.con.id, {prev: prev, new: elm.con.exportReroutes()});
    }

    isUIEvent() { return true; }

    setOpPos(opID, newX, newY) {
        let op = SvInstance.pipeline.getOperatorByID(opID);
        if(op == null) return false;

        let prevX = op.posX;
        let prevY = op.posY;

        op.moveTo(newX, newY); // No need to trigger drag since groups will receive their own events (memberships)

        return op.posX !== prevX || op.posY !== prevY;
    }

    setReroutePos(conID, reroutes) {
        let con = SvInstance.pipeline.getConnectionByID(conID);
        if(con == null) return false;

        let current = con.exportReroutes();

        con.importReroutes(reroutes);

        return reroutes !== current;
    }

    async undo() {
        let changed = false;

        for(let [opID, data] of this.involvedOps.entries()) {
            if(this.setOpPos(opID, data.prev[0], data.prev[1])) changed = true;
        }

        for(let [conID, data] of this.involvedCons.entries()) {
            if(this.setReroutePos(conID, data.prev)) changed = true;
        }

        return changed;
    }

    async redo() {
        let changed = false;

        for(let [opID, data] of this.involvedOps.entries()) {
            if(this.setOpPos(opID, data.new[0], data.new[1])) changed = true;
        }

        for(let [conID, data] of this.involvedCons.entries()) {
            if(this.setReroutePos(conID, data.new)) changed = true;
        }

        return changed;
    }

    /** @param {SvOperator | ReroutePin} elm
     * @param {Object} prev **/
    update(elm, prev) {
        if(elm instanceof SvOperator) {
            let entry = this.involvedOps.get(elm.id);

            if(entry == null) this.addEntry(elm, prev);
            else entry.new = [elm.posX, elm.posY];
        } else if(elm instanceof ReroutePin) {
            let entry = this.involvedCons.get(elm.con.id);

            if(entry == null) this.addEntry(elm, prev);
            else entry.new = elm.con.exportReroutes();
        }
    }
}