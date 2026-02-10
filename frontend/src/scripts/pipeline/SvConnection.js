import {safeVal} from "@/scripts/tools/Utils";
import ConnectionMonitor from "@/scripts/features/monitor/ConnectionMonitor";
import {findRightIndex} from "@/plugins/connection-reroute-plugin/utils";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import TemplateHost from "@/scripts/tools/TemplateHost";

export default class SvConnection extends TemplateHost {
    /** @type number **/ id;

    /** @type SvSocket */ input = null; // The input socket
    /** @type SvSocket **/ output = null; // The output socket
    /** @type Array<ReroutePin> */ reroutes = [];

    /** @type ConnectionMonitor */ monitor;

    // View

    /** @type Boolean */ highlighted = false; // For indicating selected connection
    /** @type {Number|null} */ order = null; // For bringing connection component to front
    /** @type {String|null} */ strokeDashOffset = null;

    constructor(id) {
        super();

        this.id = id;

        this.monitor = new ConnectionMonitor();
    }

    // ------------------------------------------------------ View -----------------------------------------------------

    /** @return {[x1: number, y1: number, x2: number, y2: number]} **/
    getEndpoints() {
        if(this.input != null && this.output != null) {
            let inputPos = this.input.getPosition();
            let outputPos = this.output.getPosition();

            return [outputPos.x, outputPos.y, inputPos.x, inputPos.y];
        }

        return [0, 0, 0, 0];
    }

    // ---------------------------------------------------- Reroutes ---------------------------------------------------

    /** @param {Number} x
     * @param {Number} y **/
    addReroutePin(x, y) {
        let newPin = new ReroutePin(x, y, this);

        let prevReroutes = this.exportReroutes();

        const pin = { ...newPin };
        const [x1, y1, x2, y2] = this.getEndpoints();
        const points = [{ x: x1, y: y1 }, ...prevReroutes, { x: x2, y: y2 }];
        const index = findRightIndex(pin, points);

        this.reroutes.splice(index, 0, pin);

        executeEvent(EVENTS.CONNECTION_REROUTES_CHANGED, [this, prevReroutes]);
    }

    /** @param {ReroutePin} pin The pin object to remove
     * @param {Number} newX
     * @param {Number} newY
     * @param {Boolean|null} cascaded If triggered by group movement **/
    updateReroutePin(pin, newX, newY, cascaded=false) {
        let prevReroutes = this.exportReroutes();

        pin.x = newX;
        pin.y = newY;

        executeEvent(EVENTS.CONNECTION_REROUTES_CHANGED, [this, prevReroutes, cascaded]);
    }

    /** @param {ReroutePin} pin The pin object to remove **/
    removeReroutePin(pin) {
        let prevReroutes = this.exportReroutes();

        this.reroutes.splice(this.reroutes.indexOf(pin), 1);

        executeEvent(EVENTS.CONNECTION_REROUTES_CHANGED, [this, prevReroutes]);
    }

    exportReroutes() {
        let data = [];
        for(let reroute of this.reroutes) data.push({x: reroute.x, y: reroute.y});
        return data;
    }

    importReroutes(data) {
        this.reroutes = [];

        for(let entry of data) {
            this.reroutes.push(new ReroutePin(entry["x"], entry["y"], this));
        }
    }

    clearReroutes() {
        let prevReroutes = [...this.reroutes]; // Shallow copy

        this.reroutes = [];

        executeEvent(EVENTS.CONNECTION_REROUTES_CHANGED, [this, prevReroutes]);
    }

    // ------------------------------------------------ Config / Storage -----------------------------------------------

    getRuntimeSetup(){
        return {"id": this.id, "inputOp": this.input.operator.id, "inputSocket": this.input.id,
            "outputOp": this.output.operator.id, "outputSocket": this.output.id}
    }

    exportSaveData() {
        return {"id": this.id, "reroutes": this.exportReroutes(), "inputOp": this.input.operator.id, "inputSocket": this.input.id,
            "outputOp": this.output.operator.id, "outputSocket": this.output.id};
    }

    importSaveData(data) {
        // Don't import id in case it was changed during con creation!

        this.importReroutes(safeVal(data["reroutes"], []));
    }
}

export class ReroutePin {
    /** @param {Number} x
    * @param {Number} y
    * @param {SvConnection} con */
    constructor(x, y, con) {
        this.x = x;
        this.y = y;
        this.con = con;
    }
}