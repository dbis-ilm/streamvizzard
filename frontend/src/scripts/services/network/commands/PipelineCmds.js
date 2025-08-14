import {Command} from "@/scripts/services/network/commands/Command";
import {NetworkService} from "@/scripts/services/network/NetworkService";
import {PipelineService, PIPELINE_STATUS} from "@/scripts/services/pipelineState/PipelineService";

class PipelineStatusCMD extends Command {
    constructor() {
        super("status");
    }

    handleCommand(data) {
        let status = data["status"];

        if(status === "starting") {
            PipelineService.setPipelineStatus(PIPELINE_STATUS.STARTING);
        } else if(status === "started") {
            PipelineService.setPipelineStatus(PIPELINE_STATUS.STARTED);
        } else if(status === "stopping") {
            PipelineService.setPipelineStatus(PIPELINE_STATUS.STOPPING);
        }  else if(status === "stopped") {
            PipelineService.setPipelineStatus(PIPELINE_STATUS.STOPPED);
        }
    }
}

class PipelineAdvisorSugCMD extends Command {
    constructor() {
        super("opAdvisorSug");
    }

    handleCommand(data) {
        let op = PipelineService.getOperatorByID(data["opID"]);

        if(op != null) op.component.setAdvisorSuggestions(op, data["sugs"]);
    }
}

export function registerPipelineCMDs() {
    NetworkService.registerCommand(new PipelineStatusCMD());
    NetworkService.registerCommand(new PipelineAdvisorSugCMD());
}