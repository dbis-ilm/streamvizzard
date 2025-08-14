import {Service} from "@/scripts/services/Services";
import {system} from "@/main";
import AreaPlugin from "rete-area-plugin";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import {initializePipelineExporter} from "@/scripts/services/dataExport/PipelineExporter";
import {SV_VERSION} from "@/scripts/streamVizzard";

// Responsible for collecting data across the system to store in the save files
// Also used for restoring previous states from save files by applying loaded data


class _DataExportService extends Service {
    constructor() {
        super("DataExportService");

        this.dataExporters = [];
    }

    getEditorVersionID() {
        return "svEditor@1.0.0";
    }

    registerDataExporter(key, getFunction, setFunction) {
        this.dataExporters.push({"key": key, "exporter": {"getData": getFunction, "setData": setFunction}});
    }

    getDataExporter() {
        return this.dataExporters;
    }

    getOperatorSaveData(node) {
        let data = node.component.getData(node);

        let inputs = [];
        for(let input of node.inputs) {
            inputs.push({"id": input[1].key, "name": input[1].name});
        }

        let outputs = [];
        for(let output of node.outputs) {
            outputs.push({"id": output[1].key, "name": output[1].name});
        }

        let conData = {"inputs": inputs, "outputs": outputs};

        let obj = {"id": node.id, "path": node.component.getID(node)["path"], "uuid": node.uuid, "data": data, "dName": node.viewName, "conData": conData,
            "monitor": node.component.getMonitorData(node), "settings": node.settingsEnabled, "breakPoints": node.component.getBreakpoints(node)};

        obj["ctrlResizes"] = node.vueContext.getResizeData();

        return obj;
    }

    async loadOperatorFromSaveData(operator, sd) {
        let opData = sd.data;

        await operator.component.setData(operator, opData);

        operator.viewName = sd.dName;
        if(sd.uuid != null) operator.uuid = sd.uuid;

        if(sd.ctrlResizes !== undefined) {
            for(let r of sd.ctrlResizes) {
                operator.vueContext.resizeElement(r.id, r.data.width, r.data.height);
            }
        }

        if(sd.settings !== undefined) {
            operator.settingsEnabled = sd.settings;
        }

        //Load monitor data
        if(sd.monitor !== undefined) {
            operator.component.setMonitorData(operator, sd.monitor);
        }

        //Load breakpoints
        if(sd.breakPoints !== undefined) {
            operator.component.setBreakpoints(operator, sd.breakPoints);
        }

        //Apply connection data

        let conData = sd.conData;

        for(let input of conData.inputs) {
            let conID = input.id;
            let conName = input.name;

            //Find corresponding input with this key
            for(let opInput of operator.inputs) {
                if(opInput[1].key === conID) {
                    opInput[1].name = conName;

                    break;
                }
            }
        }

        for(let output of conData.outputs) {
            let conID = output.id;
            let conName = output.name;

            //Find corresponding input with this key
            for(let opOutput of operator.outputs) {
                if(opOutput[1].key === conID) {
                    opOutput[1].name = conName;

                    break;
                }
            }
        }
    }

    createSaveData() {
        let res = {"version": SV_VERSION};

        // Get data from registered data exporters
        for(let exp of DataExportService.getDataExporter()) res[exp.key] = exp.exporter.getData();

        return JSON.stringify(res);
    }

    async loadSaveData(json) {
        // Check for each exporter - in order - if we have a key inside the data
        for(let exp of DataExportService.getDataExporter()) {
            let data = json[exp.key];

            if(data != null) await exp.exporter.setData(data);
        }

        system.editor.view.resize();
        AreaPlugin.zoomAt(system.editor);

        executeEvent(EVENTS.PIPELINE_LOADED);
    }

}

export const DataExportService = new _DataExportService();

initializePipelineExporter(); // Needs to be very first element!
