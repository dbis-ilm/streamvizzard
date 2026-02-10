import {EVENTS, executeEvent, registerEvent} from "@/scripts/tools/EventHandler";
import {SvInstance} from "@/scripts/StreamVizzard";
import {Service} from "@/scripts/services/Service";
import {Services} from "@/scripts/services/Services";
import {GenericUpdatePU, OperatorAddedPU, OperatorRemovedPU} from "@/scripts/services/pipelineUpdates/PipelineUpdates";

const UPDATE_FREQUENCY_MS = 250;

// Responsible for managing and sending pipelineState updates to the server

export class PipelineUpdateService extends Service {
    constructor() {
        super("PipelineUpdateService");

        this.reqPipelineUpdates = [];

        this.uniqueUpdateID = 0;
        this.listenPipelineChanges = true;
    }

    onInitialize() {
        super.onInitialize();

        window.setInterval(() => {
            if(SvInstance.pipeline.isPipelineStarted()) {
                if (this.reqPipelineUpdates.length > 0) {
                    const copy = this.reqPipelineUpdates;
                    let updateID = this.uniqueUpdateID;

                    this.reqPipelineUpdates = [];
                    this.uniqueUpdateID++;

                    const updateData = [];
                    for(let u of copy) updateData.push(u.createSocketData());

                    this._sendPipelineUpdates(updateData, updateID);
                }
            } else {
                this.reqPipelineUpdates = [];
                this.uniqueUpdateID = 0;
            }
        }, UPDATE_FREQUENCY_MS);

        registerEvent(EVENTS.OP_CREATED,
            /** @param {SvOperator} op */ (op) =>
                this.registerPipelineUpdate(new OperatorAddedPU(op.id, op.getRuntimeSetup())));

        registerEvent(EVENTS.OP_REMOVED,
            /** @param {SvOperator} op */ (op) =>
            this.registerPipelineUpdate(new OperatorRemovedPU(op.id)));

        registerEvent(EVENTS.DEBUG_UI_EVENT_REGISTERED, () => {
            this.registerPipelineUpdate(new GenericUpdatePU());
        })
    }

    registerPipelineUpdate(update) {
        SvInstance.pipeline.errorMsg = null; // Reset error if we perform a change

        executeEvent(EVENTS.PIPELINE_MODIFIED, update);

        if(!this._canRegisterPipelineUpdate()) return false;

        if(this.reqPipelineUpdates.length > 0) {
            const lastElm = this.reqPipelineUpdates[this.reqPipelineUpdates.length - 1];
            if(lastElm.checkUpdate(update)) return;
        }

        this.reqPipelineUpdates.push(update);

        return true;
    }

    getUniqueUpdateID() {
        return this.uniqueUpdateID;
    }

    listenForPipelineChanges(listen) {
        this.listenPipelineChanges = listen;
    }

    _canRegisterPipelineUpdate() {
        return SvInstance.pipeline.isPipelineStarted() && this.listenPipelineChanges;
    }

    _sendPipelineUpdates(updateData, updateID) {
        const data = {};
        data["updates"] = updateData;
        data["cmd"] = "pipelineUpdate";
        data["updateID"] = updateID;

        Services.Network.socketSend(data);
    }
}
