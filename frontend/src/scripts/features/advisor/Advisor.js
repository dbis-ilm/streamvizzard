import {safeVal} from "@/scripts/tools/Utils";
import {Services} from "@/scripts/services/Services";
import {SvInstance} from "@/scripts/StreamVizzard";

export class Advisor {
    constructor() {
        this.enabled = false;

        // Show (open) advisor panel on sidebar
        this.showSidebar = true;
    }

    toggle(enabled) {
        this.enabled = enabled;

        this.onConfigChanged();
    }

    onConfigChanged() {
        // If we add more properties, we can add reactive change listener
        if (SvInstance.pipeline.isPipelineStarted()) Services.Network.changeAdvisorConfig(this.getConfig());
    }

    getConfig() {
        return {
            "enabled": this.enabled
        };
    }

    exportSaveData() {
        return {
            "enabled": this.enabled,
            "showSidebar": this.showSidebar
        };
    }

    importSaveData(data) {
        this.enabled = safeVal(data["enabled"], this.enabled);
        this.showSidebar = safeVal(data["showSidebar"], this.showSidebar);
    }
}