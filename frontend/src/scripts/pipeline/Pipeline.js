import {EVENTS, executeEvent, INTERACTION, registerEvent} from "@/scripts/tools/EventHandler";
import {v4} from "uuid";
import SvConnection from "@/scripts/pipeline/SvConnection";
import Vue from "vue";
import {Services} from "@/scripts/services/Services";
import {ConnectionAddedPU, ConnectionRemovedPU} from "@/scripts/services/pipelineUpdates/PipelineUpdates";
import {Group} from "@/scripts/pipeline/Group";
import {SvInstance} from "@/scripts/StreamVizzard";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";
import {migrateOperatorSaveData} from "@/scripts/services/dataExport/Migrations";
import {safeVal} from "@/scripts/tools/Utils";

export class Pipeline {
    constructor() {
        // Operators

        /** @type Array<SvOperator> **/
        this.operators = []; // order = visual rendering
        /** @type {Map<number, SvOperator>}**/
        this._operatorLookup = new Map();

        this._uniqueOperatorIDCounter = 1;

        // Connections

        /** @type Array<SvConnection> **/
        this.connections = [];
        /** @type {Map<number, SvConnection>}**/
        this._connectionLookup = new Map(); // Non-reactive

        this._uniqueConnectionIDCounter = 1;

        // Groups

        /** @type Array<Group> **/
        this.groups = [];
        /** @type {Map<number, Group>}**/
        this._groupLookup = new Map();

        this._uniqueGroupIDCounter = 1;

        // ---

        /** @type {string|null} **/
        this.errorMsg = null;

        this.pipelineStatus = PIPELINE_STATUS.STOPPED;

        this.pipelineMetaData = new PipelineMetaData();
    }

    initialize() {
        registerEvent(EVENTS.PIPELINE_MODIFIED, (update) => update.changesSemantic() ? this.pipelineMetaData.generateNewID() : null);

        this._initializeGroups();
    }

    clearPipeline() {
        this.pipelineMetaData.clear();

        this.operators = [];
        this._operatorLookup.clear();

        this.connections = [];
        this._connectionLookup.clear();

        this.groups = [];
        this._groupLookup.clear();

        this._uniqueOperatorIDCounter = 1;
        this._uniqueGroupIDCounter = 1;
        this._uniqueConnectionIDCounter = 1;

        this.errorMsg = null;

        executeEvent(EVENTS.PIPELINE_CLEARED);
    }

    // --------------- Pipeline Status ---------------

    setPipelineStatus(status) {
        let statusChanged = status !== this.pipelineStatus;

        this.pipelineStatus = status;

        if(statusChanged) executeEvent(EVENTS.PIPELINE_STATUS_CHANGED, this.pipelineStatus);
    }

    isPipelineStarted() {
        return this.pipelineStatus === PIPELINE_STATUS.STARTED;
    }

    isPipelineStopped() {
        return this.pipelineStatus === PIPELINE_STATUS.STOPPED;
    }

    isPipelineStarting() {
        return this.pipelineStatus === PIPELINE_STATUS.STARTING;
    }

    isPipelineStopping() {
        return this.pipelineStatus === PIPELINE_STATUS.STOPPING;
    }

    // --------------- Operators ---------------

    /** @param {Definition} definition
     * @param {number|null} id
     * @param {number} x
     * @param {number} y
     * @returns {SvOperator|null} **/
    async createOperator(definition, {id = null, x = 0, y = 0} = {}) {
        if(id != null && this.getOperatorByID(id) != null) return null; // Already exists

        if(id == null) id = this._uniqueOperatorIDCounter;
        else this._uniqueOperatorIDCounter = Math.max(id, this._uniqueOperatorIDCounter);

        this._uniqueOperatorIDCounter++;

        let op = new Vue.observable(new SvOperator(id, definition)); // Make connection object reactive
        op.initialize();

        op.order = this.operators.length; // By default, each new operators gets highest current order
        op.posX = x;
        op.posY = y;

        definition.build(op);

        this.operators.push(op);
        this._operatorLookup.set(op.id, op);

        await Vue.nextTick(); // Give time for the operator to render

        executeEvent(EVENTS.OP_CREATED, op);

        return op;
    }

    /** @returns {Promise<SvOperator|null>} **/
    async createOperatorFromSaveData(opData, keepID = true) {
        opData = migrateOperatorSaveData(opData);

        let definition = SvInstance.modules.getOperatorDefinition(opData["definition"]);

        if(definition == null) {
            console.info("Failed to load operator by path: " + opData["definition"]);

            return null;
        }

        let props = {"x": opData["posX"], "y": opData["posY"]};
        if(keepID) props["id"] = opData["id"];

        let op = await this.createOperator(definition, props);

        op.importSaveData(opData);

        if(keepID) op.uuid = safeVal(opData["uuid"], op.uuid);

        return op;
    }

    /** @param {SvOperator} operator **/
    deleteOperator(operator) {
        let op = this.getOperatorByID(operator.id);
        if(op == null) return false;

        // First clear all connections

        for(let input of op.inputs) input.clearConnections();
        for(let output of op.outputs) output.clearConnections();

        // Now remove operator

        this._operatorLookup.delete(operator.id);
        this.operators.splice(this.operators.indexOf(op), 1);

        if(SvInstance.editor.selectedOperator === op) SvInstance.editor.selectEditorObject(null);

        executeEvent(EVENTS.OP_REMOVED, op);

        return true;
    }

    /** @returns {SvOperator|null} The group if present **/
    getOperatorByID(opID) {
        return this._operatorLookup.get(opID) || null;
    }

    /** Promotes the given op to the highest (visual) order */
    alignOperatorOrder(op) {
        if(this.getOperatorByID(op.id) == null) return; // No part of pipeline anymore

        // Create a copy of the operator array since removing and adding the operator will force
        // a re-render of the vue component and drops the pointer events. Sort by the order ASC to respect current order

        let orderArray = this.operators.slice().sort((a,b) => a.order - b.order);

        // Promotes this operator to the highest order

        let opIdx = orderArray.indexOf(op);
        orderArray.push(orderArray.splice(opIdx, 1)[0]);

        // Update order values

        for(let idx = 0; idx < orderArray.length; idx++) {
            /** @type SvOperator */
            let op = orderArray[idx];

            op.order = idx;
        }
    }

    // --------------- Connections ---------------

    /** @param {SvSocket} input
     * @param {SvSocket} output
     * @param {Object} [options={}]
     * @param {number|null} [options.id]
     * @return {SvConnection|null} **/
    createConnection(input, output, {id} = {}) {
        if(id != null && this.getConnectionByID(id) != null) return null; // Already exists

        if(this.validateConnection(input, output) != null) return null;

        if(id == null) id = this._uniqueConnectionIDCounter;
        else this._uniqueConnectionIDCounter = Math.max(id, this._uniqueConnectionIDCounter);

        this._uniqueConnectionIDCounter++;

        let con = new Vue.observable(new SvConnection(id)); // Make connection object reactive

        if(input != null) input.addConnection(con);
        if(output != null) output.addConnection(con);

        this.connections.push(con);
        this._connectionLookup.set(con.id, con);

        Services.PipelineUpdates.registerPipelineUpdate(new ConnectionAddedPU(con));

        executeEvent(EVENTS.CONNECTION_CREATED, con);

        return con;
    }

    /** @returns {SvConnection|null} **/
    createConnectionFromSaveData(conData, skipWarning=false) {
        let inputOp = SvInstance.pipeline.getOperatorByID(conData["inputOp"]);
        if(inputOp == null) {
            if(!skipWarning) console.info("Failed to load input operator by ID: " + conData["inputOp"]);

            return null;
        }

        let outputOp = SvInstance.pipeline.getOperatorByID(conData["outputOp"]);
        if(outputOp == null) {
            if(!skipWarning) console.info("Failed to load output operator by ID: " + conData["inputOp"]);

            return null;
        }

        let inSocket = inputOp.getSocketByID(conData["inputSocket"], true);
        if(inSocket == null) {
            if(!skipWarning) console.info("Failed to load input socket " + conData["inputSocket"] + " of operator " + inputOp.id);

            return null;
        }

        let outSocket = outputOp.getSocketByID(conData["outputSocket"], false);
        if(outSocket == null) {
            if(!skipWarning) console.info("Failed to load output socket " + conData["outputSocket"] + " of operator " + outputOp.id);

            return null;
        }

        let con = this.createConnection(inSocket, outSocket, {id: conData["id"]});
        if(con != null) con.importSaveData(conData);

        return con;
    }

    /** @param {SvConnection} con **/
    deleteConnection(con) {
        if(this.getConnectionByID(con.id) == null) return false; // Not present in pipeline

        this._connectionLookup.delete(con.id);
        this.connections.splice(this.connections.indexOf(con), 1);

        con.input.removeConnection(con);
        con.output.removeConnection(con);

        Services.PipelineUpdates.registerPipelineUpdate(new ConnectionRemovedPU(con.id));

        executeEvent(EVENTS.CONNECTION_REMOVED, con);

        return true;
    }

    /** @param {SvSocket} input
     * @param {SvSocket} output */
    validateConnection(input, output) {
        if(input.operator === output.operator) return "Can't self-connect operators!";
        else if(input.input === output.input) return "Incompatible socket types!";

        // Check for socket types

        if(!input.definition.type.isCompatibleWith(output.definition.type)) return "Incompatible data types!";

        // Check for cyclic connection

        let startOp = output.operator;

        let visitOutputs = function (currentOp) {
            for(let outSock of currentOp.outputs) {
                for(let con of outSock.connections) {
                    if(startOp === con.input.operator) return false;

                    if (!visitOutputs(con.input.operator)) return false;
                }
            }

            return true;
        }

        let cyclic = !visitOutputs(input.operator);

        if(cyclic) return "Cyclic operator connection!";

        return null;
    }

    /** @returns {SvConnection|null} The connection if present **/
    getConnectionByID(conID) {
        return this._connectionLookup.get(conID) || null;
    }

    // --------------- Groups ----------------

    _initializeGroups() {
        registerEvent(EVENTS.OP_INTERACTED, (op, interaction) => {
            // If any op in the selection already has a group, we skip

            for(let obj of SvInstance.editor.focusedObjects) {
                if(obj instanceof SvOperator && obj.group != null) return;
            }

            if(interaction === INTERACTION.DRAGGING) {
                // During dragging, check which group we (our selection) are hovering and mark it

                let hoverGroup = null;

                for(let group of this.groups.values()) {
                    group.nodeAddHover = false;

                    if(hoverGroup == null) {
                        for(let obj of SvInstance.editor.focusedObjects) {
                            if(obj instanceof SvOperator && group.intersectsOp(obj)) {
                                hoverGroup = group;

                                break;
                            }
                        }
                    }
                }

                if(hoverGroup != null) hoverGroup.nodeAddHover = true;

            } else if(interaction === INTERACTION.DRAG_END) {
                // After node finishes dragging, add selection to hovered group

                for(let group of this.groups.values()) {
                    if(!group.nodeAddHover) continue;

                    for(let obj of SvInstance.editor.focusedObjects) {
                        if (obj instanceof SvOperator) group.addOperator(obj);
                    }
                }

                // Reset potential hover for all groups
                for(let group of this.groups.values()) group.nodeAddHover = false;
            }
        });

        registerEvent(EVENTS.OP_MOVED, (op) => {
            // If node is member of a group, update transform to match new node pos

            if(op.group != null) op.group.updateTransform();
        });

        registerEvent(EVENTS.OP_SIZE_CHANGED, (op) => {
            if(op.group == null) return;

            op.group.updateTransform(op);
        });

        registerEvent(EVENTS.OP_REMOVED, op => {
            if(op.group == null) return;

            op.group.removeOperator(op);
        }, 0); // Call this event before other callbacks (history) to first remove node from group
    }

    /** @param {SvOperator|null} initialOp
     * @param {Number|id} id
     * @returns {Group | null} **/
    createGroup(initialOp=null, id=null) {
        if(id != null && this.getGroupById(id) != null) return null; // Already exists
        if(initialOp != null && initialOp.group != null) return null; // Already in group

        let newID = id != null ? id : this._uniqueGroupIDCounter;
        this._uniqueGroupIDCounter = Math.max(this._uniqueGroupIDCounter, newID) + 1;

        let newGroup = new Group(newID);

        this.groups.push(newGroup);
        this._groupLookup.set(newGroup.id, newGroup);

        if(initialOp != null) newGroup.addOperator(initialOp);

        return newGroup;
    }

    createGroupFromSaveData(data, allowEmpty=false) {
        let operators = data["operators"].map(id => this.getOperatorByID(id)).filter(node => node != null);
        if(operators.length === 0 && !allowEmpty) return;

        let gp = SvInstance.pipeline.createGroup(null, data["id"]);
        gp.title = data["title"];

        for(let op of operators) gp.addOperator(op);
    }

    /** @param {Group} group **/
    deleteGroup(group) {
        if(this.getGroupById(group.id) == null) return; // No part of pipeline

        this.groups.splice(this.groups.indexOf(group), 1);
        this._groupLookup.delete(group.id);

        if(Object.keys(group).length > 0) group.remove();
    }

    /** @returns {Group|null} The group if present **/
    getGroupById(id) {
        return this._groupLookup.get(id) || null;
    }

    // --------------- Utility ---------------

    getRuntimeConfig() {
        return {
            "uuid": this.pipelineMetaData.getUUID(),
            "operators": this.operators.map(op => op.getRuntimeSetup()),
            "connections": this.connections.map(con => con.getRuntimeSetup()),
        };
    }

    // ----------------------------------------------------- Storage ---------------------------------------------------

    exportSaveData() {
        let opData = [];

        for(let op of this.operators) opData.push(op.exportSaveData());

        let conData = [];

        for(let con of this.connections) conData.push(con.exportSaveData());

        let groupData = [];

        for(let group of this.groups) groupData.push(group.exportSaveData());

        return {"operators": opData, "connections": conData,
            "groups": groupData,
            "meta": this.pipelineMetaData};
    }

    async importSaveData(data) {
        this.clearPipeline();

        for(let opData of safeVal(data["operators"], [])) await this.createOperatorFromSaveData(opData);

        for(let conData of safeVal(data["connections"], [])) this.createConnectionFromSaveData(conData);

        for(let group of safeVal(data["groups"], [])) this.createGroupFromSaveData(group);

        if("meta" in data) this.pipelineMetaData = Object.assign(new PipelineMetaData(), data["meta"]);
    }
}

export class PipelineMetaData {
    constructor() {
        this.pipelineName = "";
        this.pipelineUUID = "";

        this.generateNewID();
    }

    updateName(name) {
        this.pipelineName = name;
    }

    getName() {
        return this.pipelineName;
    }

    getUUID() {
        return this.pipelineUUID;
    }

    clear() {
        this.pipelineName = "";
    }

    generateNewID() {
        this.pipelineUUID = v4();
    }
}

export const PIPELINE_STATUS = {
    STARTING: 1,
    STARTED: 2,
    STOPPING: 3,
    STOPPED: 4,
}
