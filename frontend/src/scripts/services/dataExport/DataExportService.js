import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import {SvInstance} from "@/scripts/StreamVizzard";
import {migrateSaveData} from "@/scripts/services/dataExport/Migrations";
import {Service} from "@/scripts/services/Service";

// Responsible for collecting data across the system to store in the save files

export class DataExportService extends Service {
    constructor() {
        super("DataExportService");

        this.dataExporters = [];
    }

    registerDataExporter(key, getFunction, setFunction) {
        this.dataExporters.push({"key": key, "exporter": {"getData": getFunction, "setData": setFunction}});
    }

    getDataExporter() {
        return this.dataExporters;
    }

    createSaveData() {
        let res = {"svVersion": SvInstance.version};

        // Get data from registered data exporters
        for(let exp of this.getDataExporter()) res[exp.key] = exp.exporter.getData();

        return JSON.stringify(res);
    }

    async loadSaveData(saveData) {
        saveData = migrateSaveData(saveData);

        if(saveData == null) return; // Invalid, no migration supported

        // Check for each exporter - in order - if we have a key inside the data
        for(let exp of this.getDataExporter()) {
            let data = saveData[exp.key];

            if(data != null) await exp.exporter.setData(data);
        }

        SvInstance.editor.fitOperators();

        executeEvent(EVENTS.PIPELINE_LOADED);
    }
}
