import {Command} from "@/scripts/services/network/commands/Command";
import {PIPELINE_STATUS} from "@/scripts/pipeline/Pipeline";
import {SvInstance} from "@/scripts/StreamVizzard";
import {parseAdvisorSuggestion} from "@/scripts/features/advisor/AdvisorSuggestion";

class PipelineStatusCMD extends Command {
    constructor() {
        super("status");
    }

    handleCommand(data) {
        let status = data["status"];

        if(status === "starting") {
            SvInstance.pipeline.setPipelineStatus(PIPELINE_STATUS.STARTING);
        } else if(status === "started") {
            SvInstance.pipeline.setPipelineStatus(PIPELINE_STATUS.STARTED);
        } else if(status === "stopping") {
            SvInstance.pipeline.setPipelineStatus(PIPELINE_STATUS.STOPPING);
        }  else if(status === "stopped") {
            SvInstance.pipeline.setPipelineStatus(PIPELINE_STATUS.STOPPED);
        }
    }
}

class PipelineAdvisorSugCMD extends Command {
    constructor() {
        super("opAdvisorSug");
    }

    handleCommand(data) {
        let op = SvInstance.pipeline.getOperatorByID(data["opID"]);

        if(op != null) {
            let s = data["sugs"];

            if(s != null) op.updateAdvisorSuggestions(s.map(rw => parseAdvisorSuggestion(rw)).filter(s => s != null));
            else op.updateAdvisorSuggestions(null);
        }
    }
}

export function registerPipelineCMDs(service) {
    service.registerCommand(new PipelineStatusCMD());
    service.registerCommand(new PipelineAdvisorSugCMD());
}
