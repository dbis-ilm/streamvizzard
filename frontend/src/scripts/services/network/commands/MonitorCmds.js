import {Command} from "@/scripts/services/network/commands/Command";
import {onConnectionDataUpdate} from "@/scripts/features/monitor/ConnectionMonitor";
import {onOperatorDataUpdate, onOperatorHeatmapUpdate, onOperatorMessageBrokerUpdate} from "@/scripts/features/monitor/OperatorMonitor";
import {SvInstance} from "@/scripts/StreamVizzard";

class OpMonitorDataCMD extends Command {
    constructor() {
        super("opMonitorData");
    }

    handleCommand(data) {
        for(let i = 0; i < data["ops"].length; i++) {
            const entry = data["ops"][i];

            onOperatorDataUpdate(entry);
        }
    }
}

class ConMonitorDataCMD extends Command {
    constructor() {
        super("conMonitorData");
    }

    handleCommand(data) {
        for(let i = 0; i < data["cons"].length; i++)
            onConnectionDataUpdate(data["cons"][i]);
    }
}

class OpMsgBrokerDataCMD extends Command {
    constructor() {
        super("msgBroker");
    }

    handleCommand(data) {
        for(let opData of data["ops"])
            onOperatorMessageBrokerUpdate(opData);
    }
}

class OpErrorDataCMD extends Command {
    constructor() {
        super("opError");
    }

    handleCommand(data) {
        let op = SvInstance.pipeline.getOperatorByID(data["op"]);

        // Error might be null to signal, that the error was resolved

        if(op != null) op.errorMsg = data["error"];
    }
}

class HeatmapDataCMD extends Command {
    constructor() {
        super("heatmap");
    }

    handleCommand(data) {
        for(const op of data["ops"]) {
            onOperatorHeatmapUpdate(op);
        }

        SvInstance.monitor.heatmapData = data;
    }
}

export function registerMonitorCMDs(service) {
    service.registerCommand(new OpMonitorDataCMD());
    service.registerCommand(new ConMonitorDataCMD());
    service.registerCommand(new OpMsgBrokerDataCMD());
    service.registerCommand(new OpErrorDataCMD());
    service.registerCommand(new HeatmapDataCMD());
}
