import {Command} from "@/scripts/services/network/commands/Command";
import {system} from "@/main";
import {synchronizeExecution} from "@/scripts/tools/debugger/DebuggingUtils";
import {NetworkService} from "@/scripts/services/network/NetworkService";
import {safeVal} from "@/scripts/tools/Utils";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";

class DebuggerCMD extends Command {
    constructor(name) {
        super(name);
    }

    isDebuggerEnabled() {
        return safeVal(system.$refs.debugger) != null;
    }

    getDebugger() {
        return system.$refs.debugger;
    }
}

class DebuggerDataCMD extends DebuggerCMD {
    constructor() {
        super("debuggerData");
    }

    async handleCommand(data) {
        if(this.isDebuggerEnabled()) await synchronizeExecution(async () => {
            await this.getDebugger().updateTimeline(data["active"], data["maxSteps"],
                data["stepID"], data["branchID"], data["stepTime"],
                data["branchStartTime"], data["branchEndTime"], data["branchStepOffset"],
                data["memSize"], system.$refs.historyMemSlider.getMemoryLimit(),
                data["diskSize"], system.$refs.historyStorageSlider.getMemoryLimit(), data["rewindActive"]);});
    }
}

class DebuggerHistoryExCMD extends DebuggerCMD {
    constructor() {
        super("debuggerHistoryEx");
    }

    async handleCommand(data) {
        if(this.isDebuggerEnabled()) {
            await synchronizeExecution(async () => {
                await this.getDebugger().onStepExecution(data["stepID"], data["branchID"], data["op"], data["type"], data["undo"], data["stepTime"]);
            });
        }
    }
}

class DebuggerRewindCMD extends DebuggerCMD {
    constructor() {
        super("debRewind");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled()) this.getDebugger().onRewindStatusUpdate(data["status"]);
    }
}

class DebuggerUndoPendingPUCMD extends DebuggerCMD {
    constructor() {
        super("debUndoPendingPU");
    }

    async handleCommand(data) {
        await synchronizeExecution(async () => {
            if(this.isDebuggerEnabled())
                await this.getDebugger().undoPendingUpdates(data["updateIDs"]);
        })
    }
}

class DebuggerRegPUCMD extends DebuggerCMD {
    constructor() {
        super("debRegPU");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled())
            this.getDebugger().onPipelineUpdateRegistered(data["updateIDs"], data["branchID"], data["stepID"], data["stepTime"]);
    }
}

class DebuggerSplitCMD extends DebuggerCMD {
    constructor() {
        super("debSplit");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled())
            this.getDebugger().onHistorySplit(data["branchID"], data["parentID"], data["splitTime"], data["splitStep"]);
    }
}

class DebuggerHGUpdateCMD extends DebuggerCMD {
    constructor() {
        super("debHGUpdate");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled())
            this.getDebugger().onHistoryGraphUpdate(data["updates"]);
    }
}

class DebuggerTriggerBpCMD extends DebuggerCMD {
    constructor() {
        super("triggerBP");
    }

    async handleCommand(data) {
        if(this.isDebuggerEnabled()) {
            await synchronizeExecution(async () => {
                await this.getDebugger().onStepExecution(data["stepID"], data["branchID"], data["op"], data["type"], null, data["stepTime"]);

                let op = PipelineService.getOperatorByID(data["op"]);

                if(op != null) op.vueContext.setBreakpointTriggered(data["bpIndex"]);
            });
        }
    }
}

class DebuggerProvQueryResCMD extends DebuggerCMD {
    constructor() {
        super("provQueryRes");
    }

    handleCommand(data) {
        if(this.isDebuggerEnabled()) this.getDebugger().onReceiveProvenanceQueryResult(data["data"]);
    }
}

export function registerDebuggerCMDs() {
    NetworkService.registerCommand(new DebuggerDataCMD());
    NetworkService.registerCommand(new DebuggerHistoryExCMD());
    NetworkService.registerCommand(new DebuggerRewindCMD());
    NetworkService.registerCommand(new DebuggerUndoPendingPUCMD());
    NetworkService.registerCommand(new DebuggerRegPUCMD());
    NetworkService.registerCommand(new DebuggerSplitCMD());
    NetworkService.registerCommand(new DebuggerHGUpdateCMD());
    NetworkService.registerCommand(new DebuggerTriggerBpCMD());
    NetworkService.registerCommand(new DebuggerProvQueryResCMD());
}
