import {Command} from "@/scripts/services/network/commands/Command";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import {system} from "@/main";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";
import {NetworkService} from "@/scripts/services/network/NetworkService";

class OpMonitorDataCMD extends Command {
    constructor() {
        super("opMonitorData");
    }

    setOpData(opID, opData) {
        let op = PipelineService.getOperatorByID(opID);

        if(op != null) op.component.setValue(op, opData);
    }

    handleCommand(data) {
        for(let i = 0; i < data["ops"].length; i++) {
            const entry = data["ops"][i];

            const opID = entry["id"];
            const opData = entry["data"];

            this.setOpData(opID, opData);
        }
    }
}

class ConMonitorDataCMD extends Command {
    constructor() {
        super("conMonitorData");
    }

    handleCommand(data) {
        for(let i = 0; i < data["cons"].length; i++)
            executeEvent(EVENTS.CONNECTION_DATA_UPDATED, data["cons"][i]);
    }
}

class OpMsgBrokerDataCMD extends Command {
    constructor() {
        super("msgBroker");
    }

    handleCommand(data) {
        for(let op of data["ops"]) {
            let opID = op["id"];

            let opNode = PipelineService.getOperatorByID(opID);

            if(opNode != null) opNode.component.setMessageBrokerState(opNode, op["broker"]);
        }
    }
}

class OpErrorDataCMD extends Command {
    constructor() {
        super("opError");
    }

    handleCommand(data) {
        let op = PipelineService.getOperatorByID(data["op"]);

        // Error might be null to signal, that the error was resolved

        if(op != null) op.component.setError(op, data["error"]);
    }
}

class HeatmapDataCMD extends Command {
    constructor() {
        super("heatmap");
    }

    handleCommand(data) {
        for(const op of data["ops"]) {
            let opNode = PipelineService.getOperatorByID(op["op"]);

            if(opNode != null) opNode.component.setHeatmapRating(opNode, op["rating"]);
        }

        system.$refs.heatmap.onDataUpdate(data["min"], data["max"], data["steps"]);
    }
}

export function registerMonitorCMDs() {
    NetworkService.registerCommand(new OpMonitorDataCMD());
    NetworkService.registerCommand(new ConMonitorDataCMD());
    NetworkService.registerCommand(new OpMsgBrokerDataCMD());
    NetworkService.registerCommand(new OpErrorDataCMD());
    NetworkService.registerCommand(new HeatmapDataCMD());
}
