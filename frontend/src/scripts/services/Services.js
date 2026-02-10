import {EditorInputManageService} from "@/scripts/services/EditorInputManager";
import {PipelineUpdateService} from "@/scripts/services/pipelineUpdates/PipelineUpdateService";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";
import {NetworkService} from "@/scripts/services/network/NetworkService";
import {OpPresetService} from "@/scripts/services/opPresets/OpPresetService";

class _Services {
    constructor() {
        /** @type {Map<string, Service>} */
        this.services = new Map();

        this.DataExporter = new DataExportService();
        this.EditorInputManager = new EditorInputManageService();
        this.PipelineUpdates = new PipelineUpdateService();
        this.Network = new NetworkService();
        this.OpPresetService = new OpPresetService();

        this._registerServices([this.DataExporter,
            this.EditorInputManager, this.PipelineUpdates,
            this.Network, this.OpPresetService])
    }

    _registerServices(services) {
        for(let service of services) this.services.set(service.name, service);
    }

    initialize() {
        for(let service of this.services.values()) service.onInitialize();
    }
}

export const Services = new _Services();
