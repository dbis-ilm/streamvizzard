import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";

export const PIPELINE_STATUS = {
    STARTING: 1,
    STARTED: 2,
    STOPPING: 3,
    STOPPED: 4,
}

let pipelineStatus = PIPELINE_STATUS.STOPPED;

export function setPipelineStatus(status) {
    pipelineStatus = status;

    executeEvent(EVENTS.PIPELINE_STATUS_CHANGED, pipelineStatus);
}

export function getPipelineStatus() {
    return pipelineStatus;
}