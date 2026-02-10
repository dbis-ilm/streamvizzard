import {safeVal} from "@/scripts/tools/Utils";
import {OperatorConfigUpdatedPU, OperatorParamsUpdatedPU} from "@/scripts/services/pipelineUpdates/PipelineUpdates";
import {OperatorMonitor} from "@/scripts/features/monitor/OperatorMonitor";
import {v4} from "uuid";
import {Services} from "@/scripts/services/Services";
import SvSocket from "@/scripts/pipeline/SvSocket";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import {SvInstance} from "@/scripts/StreamVizzard";
import TemplateHost from "@/scripts/tools/TemplateHost";
import OperatorCompiler from "@/scripts/features/compiler/OperatorCompiler";

export default class SvOperator extends TemplateHost {
    constructor(id, definition) {
        super();

        this.id = id;
        this.uuid = v4();

        this.name = definition.displayName;

        // View

        this.posX = 0;
        this.posY = 0;
        this.width = 0;
        this.height = 0;

        /** @type {Object<String, Number>} **/
        this.resizeElemHeights = {};
        /** @type {Number|null} **/
        this.resizeElmWidth = null;

        this.order = 0; // Defines the visual order in the interface

        // Structure

        /** @type Definition **/
        this.definition = definition;

        /** @type Array<Param> **/
        this.params = [];

        /** @type Array<SvSocket> **/
        this.inputs = [];
        /** @type Array<SvSocket> **/
        this.outputs = [];

        /** @type Group **/
        this.group = null;

        // Features

        this.monitor = new OperatorMonitor(this);
        this.compiler = new OperatorCompiler(this);

        this.breakPoints = [];  // [{id: str, enabled: bool, type: str, amount: int, triggered: bool}]
        /** @type {DebugStepExecution|null} step **/
        this.debugStepNotification = null;

        // Received data

        this.errorMsg = null;
        this.advisorSuggestions = null;

        // Config

        this.showData = true;
        this.showSettings = true;
    }

    initialize() {
        // Reactive Watcher | Only works after "new Observable" was called

        SvInstance.registerWatcher(
            () => this.getConfigChangeListeners(),
            () => { this.onConfigChanged(); }, {deep: true});
    }

    resetState(keepDisplayData=false) {
        this.errorMsg = null;
        this.advisorSuggestions = null;
        this.resetTriggeredBreakPoints();
        this.debugStepNotification = null;

        this.monitor.reset(keepDisplayData);
    }

    resetTriggeredBreakPoints() {
        for(let bp of this.breakPoints) bp["triggered"] = false;
    }

    // ----------------------------------------------------- Position --------------------------------------------------

    /** @param {Number} newX
     * @param {Number} newY
     * @param {Boolean|null} cascaded If triggered by group movement */
    moveTo(newX, newY, cascaded=false) {
        let oldX = this.posX;
        let oldY = this.posY;

        this.posX = newX;
        this.posY = newY;

        if(this.posX !== oldX || this.posY !== oldY) executeEvent(EVENTS.OP_MOVED, [this, {x: oldX, y: oldY}, cascaded]);
    }

    /** Promotes the operator to the highest (visual) order */
    promoteOrder() {
        SvInstance.pipeline.alignOperatorOrder(this);
    }

    // ----------------------------------------------------- Resizes ---------------------------------------------------

    /** @param {String} key
     * @param {Number} width
     * @param {Number} height **/
    resizeElement(key, width, height) {
        let prevHeight = safeVal(this.resizeElemHeights[key]);
        let prevWidth = this.resizeElmWidth;
        let prevData = this.getResizeData();

        this.resizeElemHeights[key] = height;
        this.resizeElmWidth = width; // Same width for all elements

        if(prevWidth !== this.resizeElmWidth || prevHeight !== height) {
            this.resizeElemHeights = Object.assign({}, this.resizeElemHeights); // Triggers reactivity

            executeEvent(EVENTS.OP_RESIZED, [this, prevData]);
        }
    }

    getResizeData() {
        let cr = [];

        for(let [k, height] of Object.entries(this.resizeElemHeights)) cr.push({"id": k, "height": height});

        return {"width": this.resizeElmWidth, "entries": cr};
    }

    // ---------------------------------------------------- Sockets ----------------------------------------------------

    /** @param {SocketDef} definition
     * @param {boolean} input
     * @param {string|null} name **/
    createSocket(definition, input, name = null) {
        if(input) this.inputs.push(new SvSocket(this, definition, this.inputs.length, true, name));
        else this.outputs.push(new SvSocket(this, definition, this.outputs.length, false, name));
    }

    /** @param {SvSocket} socket **/
    removeSocket(socket) {
        socket.clearConnections();

        if(socket.input) {
            let idx = this.inputs.indexOf(socket);
            if(idx > -1) this.inputs.splice(idx, 1);
        } else {
            let idx = this.outputs.indexOf(socket);
            if(idx > -1) this.outputs.splice(idx, 1);
        }
    }

    /** @param {number} id
     *  @param {boolean} input
     *  @return {SvSocket|null} **/
    getSocketByID(id, input) {
        if(input) return (id < this.inputs.length && this.inputs.length > 0) ? this.inputs[id] : null;
        else return (id < this.outputs.length && this.outputs.length > 0) ? this.outputs[id] : null;
    }

    /** @return {Generator<SvSocket>} */
    *getAllSockets() {
        for(let input of this.inputs) yield input;

        for(let output of this.outputs) yield output;
    }

    /** @return {Generator<SvConnection>} */
    *getAllConnections() {
        for(let sock of this.getAllSockets()) {
            for(let con of sock.connections) {
                yield con;
            }
        }
    }

    // ----------------------------------------------------- Params ----------------------------------------------------

    /** @param {Param} param **/
    addParameter(param) {
        param.operator = this;

        this.params.push(param);
    }

    /** @param {Param} param
     * @param {any} oldVal **/
    onParamChanged(param, oldVal) {
        this.definition.onParamChanged(param);

        Services.PipelineUpdates.registerPipelineUpdate(new OperatorParamsUpdatedPU(this.id, this.getParamValues(), param.key));

        executeEvent(EVENTS.OP_PARAM_CHANGED, [this, param, oldVal]);
    }

    /** @return {Param} **/
    getParam(key) {
        for(let param of this.params) {
            if(param.key === key) return param;
        }

        return null;
    }

    getParamValues() {
        let data = {};

        for(let param of this.params) data[param.key] = param.getValue();

        return data;
    }

    // ----------------------------------------------------- Config ----------------------------------------------------

    onConfigChanged() {
        Services.PipelineUpdates.registerPipelineUpdate(new OperatorConfigUpdatedPU(this.id, this.getConfig()));
    }

    getConfigChangeListeners() {
        // Defines [DEEP] reactive config values to listen for changes and call onConfigChanged
        return [this.showData, this.breakPoints];
    }

    getConfig() {
        return {
            monitor: {
                enabled: this.showData,
                displayConfig: this.monitor.getDisplayConfig()
            },
            breakpoints: this.breakPoints
        }
    }

    getRuntimeSetup(){
        return {
            id: this.id,
            uuid: this.uuid,
            definition: this.definition.getFullPath(),
            params: this.getParamValues(),
            config: this.getConfig(),
        };
    }

    // ----------------------------------------------------- Storage ---------------------------------------------------

    exportSaveData() {
        let socketsIn = [];
        let socketsOut = [];

        for(let socket of this.inputs) socketsIn.push(socket.exportSaveData());
        for(let socket of this.outputs) socketsOut.push(socket.exportSaveData());

        let socketData = {"inputs": socketsIn, "outputs": socketsOut};

        return {
            "id": this.id, "uuid": this.uuid, "svVersion": SvInstance.version, "definition": this.definition.getFullPath(), "name": this.name,
            "order": this.order, "showData": this.showData, "showSettings": this.showSettings, "breakPoints": this.breakPoints,
            "monitor": this.monitor.exportSaveData(), "params": this.getParamValues(), "posX": this.posX, "posY": this.posY,
            "resizeData": this.getResizeData(), "sockets": socketData, "compiler": this.compiler.exportSaveData()};
    }

    importSaveData(data) {
        // Don't import id/uuid in case it was changed during op creation!

        this.name = safeVal(data["name"], this.name);

        this.order = safeVal(data["order"], this.order);
        this.posX = safeVal(data["posX"], this.posX);
        this.posY = safeVal(data["posY"], this.posY);

        this.showData = safeVal(data["showData"], this.showData);
        this.showSettings = safeVal(data["showSettings"], this.showSettings);
        this.breakPoints = safeVal(data["breakPoints"], this.breakPoints);

        let monitorData = safeVal(data["monitor"], null);
        if (monitorData != null) this.monitor.importSaveData(monitorData);

        let compilerData = safeVal(data["compiler"], null);
        if (compilerData != null) this.compiler.importSaveData(compilerData);

        this.resetTriggeredBreakPoints();

        // Resizes

        let resizeData = safeVal(data["resizeData"]);

        if(resizeData != null) {
            for(let rd of safeVal(resizeData["entries"], []))
                this.resizeElement(rd["id"], resizeData["width"], rd["height"]);
        }

        // Params

        for(let [key, val] of Object.entries(safeVal(data["params"], {}))) {
            let param= this.getParam(key)

            if(param != null) param.setValue(val);
        }

        // Sockets

        let socketData = safeVal(data["sockets"], {"inputs": [], "outputs": []});

        for(let sd of socketData["inputs"]) {
            let socket = this.getSocketByID(sd["id"], true);
            if(socket != null) socket.importSaveData(sd);
        }

        for(let sd of socketData["outputs"]) {
            let socket = this.getSocketByID(sd["id"], false);
            if(socket != null) socket.importSaveData(sd);
        }
    }
}
