import HistoryAction from "@/scripts/tools/editorHistory/HistoryAction";
import {SvInstance} from "@/scripts/StreamVizzard";

class ConnectionAction extends HistoryAction {
    /** @param {SvConnection} con **/
    constructor(con) {
        super();

        this.connectionID = con.id;

        this.saveData = null;
    }

    removeConnection() {
        let con = SvInstance.pipeline.getConnectionByID(this.connectionID);
        if(con == null) return false;

        this.saveData = con.exportSaveData();

        return SvInstance.pipeline.deleteConnection(con);
    }

    createConnection() {
        return SvInstance.pipeline.createConnectionFromSaveData(this.saveData) != null;
    }

    isPipelineChangeEvent() { return true; }
}

export class AddConnectionAction extends ConnectionAction {
    async undo() {
        return this.removeConnection();
    }

    async redo() {
        return this.createConnection();
    }
}

export class RemoveConnectionAction extends ConnectionAction {
    /** @param {SvConnection} con **/
    constructor(con) {
        super(con);

        this.saveData = con.exportSaveData();
    }

    async undo() {
        return this.createConnection();
    }

    async redo() {
        return this.removeConnection();
    }
}

export class RerouteChangeAction extends ConnectionAction {
    /** @param {SvConnection} con
     * @param {Array<Object>} prevReroutes **/
    constructor(con, prevReroutes) {
        super(con);

        this.reroutes = con.exportReroutes();
        this.prevReroutes = prevReroutes;
    }

    isUIEvent() { return true; }

    setReroutes(reroutes) {
        let con = SvInstance.pipeline.getConnectionByID(this.connectionID);
        if(con == null) return false;

        let current = con.exportReroutes();

        con.importReroutes(reroutes);

        return reroutes !== current;
    }

    async undo() {
        return this.setReroutes(this.prevReroutes);
    }

    async redo() {
        return this.setReroutes(this.reroutes);
    }
}
