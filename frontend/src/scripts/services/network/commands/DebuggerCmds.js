import {Command} from "@/scripts/services/network/commands/Command";
import {synchronizeExecution} from "@/scripts/features/debugger/DebuggingUtils";
import {SvInstance} from "@/scripts/StreamVizzard";
import {DebugStep} from "@/scripts/features/debugger/DebugSteps";

class DebuggerCMD extends Command {
    constructor(name) {
        super(name);
    }

    isDebuggerEnabled() {
        return SvInstance.debugger.enabled;
    }
}

class DebuggerDataCMD extends DebuggerCMD {
    constructor() {
        super("debuggerData");
    }

    async handleCommand(data) {
        if(this.isDebuggerEnabled()) await synchronizeExecution(async () => {
            let step = new DebugStep(data["branchID"], data["stepID"], data["stepOp"], data["stepType"], data["stepTime"]);
            await SvInstance.debugger.updateTimeline(step, data["active"], data["memSize"], data["diskSize"], data["maxSteps"],
                data["branchStartTime"], data["branchEndTime"], data["branchStepOffset"]);});
    }
}

class DebuggerHistoryExCMD extends DebuggerCMD {
    constructor() {
        super("debuggerHistoryEx");
    }

    async handleCommand(data) {
        if(this.isDebuggerEnabled()) {
            await synchronizeExecution(async () => {
                await SvInstance.debugger.onStepExecuted(new DebugStep(data["branchID"], data["stepID"], data["op"], data["type"], data["stepTime"]), data["undo"]);
            });
        }
    }
}

class DebuggerRewindCMD extends DebuggerCMD {
    constructor() {
        super("debRewind");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled()) SvInstance.debugger.onRewindStatusUpdate(data["status"]);
    }
}

class DebuggerUndoPendingPUCMD extends DebuggerCMD {
    constructor() {
        super("debUndoPendingPU");
    }

    async handleCommand(data) {
        await synchronizeExecution(async () => {
            if(this.isDebuggerEnabled())
                await SvInstance.debugger.undoPendingUpdates(data["updateIDs"]);
        })
    }
}

class DebuggerRegPUCMD extends DebuggerCMD {
    constructor() {
        super("debRegPU");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled())
            SvInstance.debugger.onPipelineUpdateRegistered(data["updateIDs"], data["branchID"], data["stepID"], data["stepTime"]);
    }
}

class DebuggerSplitCMD extends DebuggerCMD {
    constructor() {
        super("debSplit");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled())
            SvInstance.debugger.onHistorySplit(data["branchID"], data["parentID"], data["splitTime"], data["splitStep"]);
    }
}

class DebuggerHGUpdateCMD extends DebuggerCMD {
    constructor() {
        super("debHGUpdate");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled())
            SvInstance.debugger.onHistoryGraphUpdate(data["updates"]);
    }
}

class DebuggerTriggerBpCMD extends DebuggerCMD {
    constructor() {
        super("triggerBP");
    }

    async handleCommand(data) {
        if(this.isDebuggerEnabled()) {
            await synchronizeExecution(async () => {
                await SvInstance.debugger.onStepExecuted(new DebugStep(data["branchID"], data["stepID"], data["op"], data["type"], data["stepTime"]), null);

                let op = SvInstance.pipeline.getOperatorByID(data["op"]);

                if(op != null) {
                    // Set triggered for bp and reset all other
                    for(let bp of op.breakPoints) {
                        bp["triggered"] = bp["id"] === data["bpId"];
                    }
                }
            });
        }
    }
}

class DebuggerProvQueryResCMD extends DebuggerCMD {
    constructor() {
        super("provQueryRes");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled()) SvInstance.debugger.onReceiveProvenanceQueryResult(data["data"]);
    }
}

export function registerDebuggerCMDs(service) {
    service.registerCommand(new DebuggerDataCMD());
    service.registerCommand(new DebuggerHistoryExCMD());
    service.registerCommand(new DebuggerRewindCMD());
    service.registerCommand(new DebuggerUndoPendingPUCMD());
    service.registerCommand(new DebuggerRegPUCMD());
    service.registerCommand(new DebuggerSplitCMD());
    service.registerCommand(new DebuggerHGUpdateCMD());
    service.registerCommand(new DebuggerTriggerBpCMD());
    service.registerCommand(new DebuggerProvQueryResCMD());
}
