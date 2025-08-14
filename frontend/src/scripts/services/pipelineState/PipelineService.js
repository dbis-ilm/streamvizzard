import {Service} from "@/scripts/services/Services";
import {EVENTS, executeEvent, registerEvent} from "@/scripts/tools/EventHandler";
import {PipelineMetaData} from "@/scripts/services/pipelineState/PipelineMetaData";
import Vue from "vue";

// Manages information about the pipelineState status, operators, connections, and metadata

class _PipelineService extends Service {
    constructor() {
        super("PipelineService");

        this.operatorLookup = new Map();

        this.connectionLookup = new Map();
        this.uniqueConnectionIDCounter = 0;

        this.pipelineStatus = PIPELINE_STATUS.STOPPED;

        this.pipelineMetaData = new PipelineMetaData();

        registerEvent(EVENTS.CLEAR_PIPELINE, () => this.clearPipeline);
        registerEvent(EVENTS.PIPELINE_MODIFIED, (update) => update.changesSemantic() ? this.pipelineMetaData.generateNewID() : null);
    }

    clearPipeline() {
        this.pipelineMetaData.clear();
        this.operatorLookup.clear();
        this.connectionLookup.clear();
    }

    // --------------- Pipeline Status ---------------

    setPipelineStatus(status) {
        let statusChanged = status !== this.pipelineStatus;

        this.pipelineStatus = status;

        if(statusChanged) executeEvent(EVENTS.PIPELINE_STATUS_CHANGED, this.pipelineStatus);
    }

    getPipelineStatus() {
        return this.pipelineStatus;
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

    registerOperator(opID, op) {
        this.operatorLookup.set(opID, op);
    }

    deleteOperator(opID) {
        this.operatorLookup.delete(opID);
    }

    getOperatorByID(opID) {
        if(this.operatorLookup.has(opID)) return this.operatorLookup.get(opID);

        return null;
    }

    getAllOperators() {
        return this.operatorLookup.values();
    }

    // --------------- Connections ---------------

    registerConnection(con) {
        if(con.id == null) con.id = this.uniqueConnectionIDCounter;
        else this.uniqueConnectionIDCounter = Math.max(con.id, this.uniqueConnectionIDCounter);

        this.uniqueConnectionIDCounter++;

        this.connectionLookup.set(con.id, con);
    }

    deleteConnection(conID) {
        this.connectionLookup.delete(conID);
    }

    getConnectionByID(conID) {
        if(this.connectionLookup.has(conID)) return this.connectionLookup.get(conID);

        return null;
    }

    getConnectionBetween(inOpID, outOpID, inSocketKey, outSocketKey) {
        let inNode = this.getOperatorByID(inOpID);

        if(inNode == null) return null;

        let inSock = inNode.component.getSocketByKey(inNode, inSocketKey);

        if(inSock == null) return null;

        for(let con of inSock.connections) {
            if(con.output.node.id === outOpID && con.output.key === outSocketKey) return con;
        }

        return null;
    }

    getAllConnections() {
        return this.connectionLookup.values();
    }

    // --------------- Utility ---------------

    createPipelineData() {
        const data = {
            "operators": [],
            "uuid": this.pipelineMetaData.getUUID(),
        };

        for (const v of this.getAllOperators()) {
            data.operators.push(v.component.getPipelineData(v));
        }

        return data;
    }
}

export const PIPELINE_STATUS = {
    STARTING: 1,
    STARTED: 2,
    STOPPING: 3,
    STOPPED: 4,
}

// Add reactivity to this object for other components to listen to
export const PipelineService = Vue.observable(new _PipelineService());
