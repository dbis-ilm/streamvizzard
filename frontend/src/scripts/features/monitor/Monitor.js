import {safeVal} from "@/scripts/tools/Utils";
import {Services} from "@/scripts/services/Services";
import {initializeConnectionMonitor} from "@/scripts/features/monitor/ConnectionMonitor";
import {initializeOpMonitor} from "@/scripts/features/monitor/OperatorMonitor";
import {SvInstance} from "@/scripts/StreamVizzard";
import {Heatmap} from "@/scripts/features/monitor/Heatmap";

export class Monitor {
    constructor() {
        this.enabled = true;
        this.trackStats = false;

        this.heatmap = new Heatmap();

        // Show (open) advisor panel on sidebar
        this.showSidebar = true;
        this.showSidebarStats = true;
        this.showSidebarTransformer = false;
        this.sideBarStatMode = null; // Last selected statistics mode
    }

    initialize() {
        initializeConnectionMonitor();
        initializeOpMonitor();

        SvInstance.registerWatcher(
            () => this.getConfigChangeListeners(),
            () => { this.onConfigChanged(); },
            {deep: true}
        );
    }

    // ----------------------------------------------- Backend Reactivity ----------------------------------------------

    onConfigChanged() {
        if (SvInstance.pipeline.isPipelineStarted()) Services.Network.changeMonitorConfig(this.getConfig());
    }

    getConfigChangeListeners() {
        // Defines reactive config values to listen for changes and call onConfigChanged
        return [this.enabled, this.trackStats];
    }

    // -----------------------------------------------------------------------------------------------------------------

    getConfig() {
        return {
            "enabled": this.enabled,
            "trackStats": this.trackStats,
        };
    }

    exportSaveData() {
        return {
            "enabled": this.enabled,
            "showSidebar": this.showSidebar,
            "showSidebarStats": this.showSidebarStats,
            "showSidebarTransformer": this.showSidebarTransformer,
            "sideBarStatMode": this.sideBarStatMode,
            "trackStats": this.trackStats,
        };
    }

    importSaveData(data) {
        this.enabled = safeVal(data["enabled"], this.enabled);
        this.showSidebar = safeVal(data["showSidebar"], this.showSidebar);
        this.showSidebarStats = safeVal(data["showSidebarStats"], this.showSidebarStats);
        this.showSidebarTransformer = safeVal(data["showSidebarTransformer"], this.showSidebarTransformer);
        this.sideBarStatMode = safeVal(data["sideBarStatMode"]);
        this.trackStats = safeVal(data["trackStats"], this.trackStats);
    }
}
