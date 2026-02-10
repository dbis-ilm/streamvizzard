import {safeVal} from "@/scripts/tools/Utils";
import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import {Services} from "@/scripts/services/Services";
import {SvInstance} from "@/scripts/StreamVizzard";
import {DebugStepExecution} from "@/scripts/features/debugger/DebugSteps";

export class Debugger {
    constructor() {
        // Config

        this.enabled = false;
        this.enableStepNotifications = false;
        this.allowHistoryPreview = false;
        this.rewindUseStepTime = true;
        this.provenanceEnabled = false;
        this.provAwaitUpdates = false;

        this.memoryLimit = null;  // null = infinite
        this.storageLimit = null;  // null = infinite
        this.rewindSpeed = 1;

        this.showSidebar = true;

        // Debug State

        this.historyActive = false; // Active=pipeline paused for debugging

        this.rewinding = false;
        this.rewindForward = false;

        this.currentStorageSize = 0;
        this.currentMemSize = 0;

        // Callbacks TODO: Rework to remove them! [Extract HistoryGraph logic to standalone js class?]

        this.onResetCb = null;
        this.onStepExecutedCb = null;
        this.updateHistoryCb = null;
        this.undoPendingUpdatesCb = null;
        this.historyGraphUpdateCb = null;
        this.pipelineUpdateRegCb = null;
        this.onHistorySplitCb = null;
        this.receiveProvResCb = null;
    }

    initialize() {
        // Ensure, we reset breakPointTrigger when pipeline stops or history state changes

        let resetBreakPointTriggers = () => {
            for(let op of SvInstance.pipeline.operators) op.resetTriggeredBreakPoints();
        }

        registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, () => {
            resetBreakPointTriggers();
            this.resetState();
        });

        SvInstance.registerWatcher(() => [this.historyActive, this.enabled, this.rewinding],() => {
            if(!this.enabled || !this.historyActive || this.rewinding) resetBreakPointTriggers();

            if(!this.enabled) this.resetState();
        });

        SvInstance.registerWatcher(
            () => this.getConfigChangeListeners(),
            () => { this.onConfigChanged(); },
            {deep: true}
        );
    }

    resetState() {
        this.historyActive = false;

        this.rewinding = false;
        this.rewindForward = false;

        this.currentMemSize = 0;
        this.currentStorageSize = 0;

        if(this.onResetCb != null) this.onResetCb();
    }

    // ------------------------------------------------ Backend Responses ----------------------------------------------

    /** @param {DebugStep} step
     * @param {Boolean} active
     * @param {Number} currentMemSize
     * @param {Number} currentStorageSize
     * @param {Number} maxBranchSteps
     * @param {Number} branchStartTime
     * @param {Number} branchEndTime
     * @param {Number} branchStepOffset**/
    async updateTimeline(step, active, currentMemSize, currentStorageSize,
                         maxBranchSteps, branchStartTime, branchEndTime, branchStepOffset) {
        // Called during execution of the pipeline

        this.historyActive = active;

        this.currentMemSize = currentMemSize;
        this.currentStorageSize = currentStorageSize;

        if(this.updateHistoryCb != null) await this.updateHistoryCb(step, maxBranchSteps, branchStartTime, branchEndTime, branchStepOffset);
    }

    /** @param {DebugStep} step
     *  @param {Boolean|null} undo Null if normal execution, else true for undo, false for redo**/
    async onStepExecuted(step, undo) {
        // Called during traversing or breakpoint triggering

        if(this.onStepExecutedCb != null) await this.onStepExecutedCb(step);

        if(this.enableStepNotifications) {
            let op = SvInstance.pipeline.getOperatorByID(step.opID);
            if(op != null) op.debugStepNotification = new DebugStepExecution(step, undo);
        }
    }

    /** @param {Number} status **/
    onRewindStatusUpdate(status) {
        // null=No, 1=Forward, 2=Backward
        this.rewinding = status != null;
        this.rewindForward = status === 1;
    }

    async undoPendingUpdates(updateIDs) {
        if(this.undoPendingUpdatesCb != null) await this.undoPendingUpdatesCb(updateIDs);
    }

    onHistoryGraphUpdate(updates) {
        if(this.historyGraphUpdateCb != null) this.historyGraphUpdateCb(updates);
    }

    onPipelineUpdateRegistered(updateIDs, branchID, stepID, stepTime) {
        if(this.pipelineUpdateRegCb != null) this.pipelineUpdateRegCb(updateIDs, branchID, stepID, stepTime);
    }

    onHistorySplit(newBranchID, parentBranchID, splitTime, splitStepID) {
        if(this.onHistorySplitCb != null) this.onHistorySplitCb(newBranchID, parentBranchID, splitTime, splitStepID);
    }

    onReceiveProvenanceQueryResult(data) {
        if(this.receiveProvResCb != null) this.receiveProvResCb(data);
    }

    // -----------------------------------------------------------------------------------------------------------------

    /** @param {Number} targetBranch
     * @param {Number} targetStep **/
    traverseTo(targetBranch, targetStep) {
        if (SvInstance.pipeline.isPipelineStarted())
            Services.Network.socketSend({
                "cmd": "debuggerStepChange",
                "targetStep": targetStep,
                "targetBranch": targetBranch,
            })
    }

    /** @param {Boolean} historyActive
     * @param {Boolean} rewinding
     * @param {Boolean} rewindForward**/
    changeState(historyActive, rewinding, rewindForward) {
        // null=No, 1=Forward, 2=Backward
        let historyRewind = !rewinding ? null : (rewindForward ? 1: 2);

        if (SvInstance.pipeline.isPipelineStarted())
            Services.Network.changeDebuggerState({
                "historyActive": historyActive,
                "historyRewind": historyRewind
            });
    }

    requestStep(targetBranch, targetTime, callback) {
        if (SvInstance.pipeline.isPipelineStarted()) {
            Services.Network.requestDebuggerStep({
                "targetTime": targetTime,
                "targetBranch": targetBranch,
            }).then(function (data) {
                callback(data["branchID"], data["stepID"]);
            });
        }
    }

    executeProvQuery(query) {
        if (SvInstance.pipeline.isPipelineStarted())
            Services.Network.executeProvenanceQuery(query);
    }

    // ------------------------------------------------ Config / Storage -----------------------------------------------

    getConfigChangeListeners() {
        // Defines reactive config values to listen for changes and call onConfigChanged
        return [this.enabled, this.rewindUseStepTime, this.provenanceEnabled, this.provAwaitUpdates,
            this.memoryLimit, this.storageLimit, this.rewindSpeed];
    }

    onConfigChanged() {
        // This is called when any of the class properties changes! (also showSidebar)
        if (SvInstance.pipeline.isPipelineStarted()) Services.Network.changeDebuggerConfig(this.getConfig());
    }

    getConfig() {
        return {
            "enabled": this.enabled,
            "debuggerMemoryLimit": this.memoryLimit,
            "debuggerStorageLimit": this.storageLimit,
            "historyRewindSpeed": this.rewindSpeed,
            "historyRewindUseStepTime": this.rewindUseStepTime,
            "provenanceEnabled": this.provenanceEnabled,
            "provenanceAwaitUpdates": this.provAwaitUpdates
        };
    }

    exportSaveData() {
        return {
            "enabled": this.enabled,
            "showSidebar": this.showSidebar,
            "memLimit": this.memoryLimit,
            "storageLimit": this.storageLimit,
            "showStepInfo": this.enableStepNotifications,
            "allowHistPrev": this.allowHistoryPreview,
            "rewindSpeed": this.rewindSpeed,
            "rewindUseStepTime": this.rewindUseStepTime,
            "provenanceEnabled": this.provenanceEnabled,
            "provAwaitUpdates": this.provAwaitUpdates
        };
    }

    importSaveData(data) {
        this.enabled = safeVal(data["enabled"], this.enabled);
        this.showSidebar = safeVal(data["showSidebar"], this.showSidebar);
        this.allowHistoryPreview = safeVal(data["allowHistPrev"], this.allowHistoryPreview);
        this.memoryLimit = safeVal(data["memLimit"], this.memoryLimit);
        this.storageLimit = safeVal(data["storageLimit"], this.storageLimit);
        this.enableStepNotifications = safeVal(data["showStepInfo"], this.enableStepNotifications);
        this.rewindSpeed = safeVal(data["rewindSpeed"], this.rewindSpeed);
        this.rewindUseStepTime = safeVal(data["rewindUseStepTime"], this.rewindUseStepTime);
        this.provenanceEnabled = safeVal(data["provenanceEnabled"], this.provenanceEnabled);
        this.provAwaitUpdates = safeVal(data["provAwaitUpdates"], this.provAwaitUpdates);
    }
}
