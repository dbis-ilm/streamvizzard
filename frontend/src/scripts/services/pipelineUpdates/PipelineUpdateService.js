import {Service} from "@/scripts/services/Services";
import {NetworkService} from "@/scripts/services/network/NetworkService";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";

const UPDATE_FREQUENCY_MS = 250;

// Responsible for managing and sending pipelineState updates to the server

class _PipelineUpdateService extends Service {
    constructor() {
        super("PipelineUpdateService");

        this.reqPipelineUpdates = [];

        this.uniqueUpdateID = 0;
        this.listenPipelineChanges = true;
    }

    onInitialize() {
        super.onInitialize();

        window.setInterval(() => {
            if(PipelineService.isPipelineStarted()) {
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
    }

    registerPipelineUpdate(update) {
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
        return PipelineService.isPipelineStarted() && this.listenPipelineChanges;
    }

    _sendPipelineUpdates(updateData, updateID) {
        const data = {};
        data["updates"] = updateData;
        data["cmd"] = "pipelineUpdate";
        data["updateID"] = updateID;

        NetworkService.socketSend(data);
    }
}

export const PipelineUpdateService = new _PipelineUpdateService();
