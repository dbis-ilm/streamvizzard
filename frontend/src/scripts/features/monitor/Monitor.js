import {safeVal} from "@/scripts/tools/Utils";
import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import {Services} from "@/scripts/services/Services";
import {initializeConnectionMonitor} from "@/scripts/features/monitor/ConnectionMonitor";
import {initializeOpMonitor} from "@/scripts/features/monitor/OperatorMonitor";
import {SvInstance} from "@/scripts/StreamVizzard";

export class Monitor {
    constructor() {
        this.enabled = true;
        this.trackStats = false;

        this.heatmapType = 0; // Not exported
        this.heatmapData = null; // Not exported

        // Show (open) advisor panel on sidebar
        this.showSidebar = true;
        this.showSidebarStats = true;
        this.showSidebarTransformer = false;
        this.sideBarStatMode = null; // Last selected statistics mode
    }

    initialize() {
        registerEvent(EVENTS.PIPELINE_CLEARED, () => { this.heatmapType = 0; });

        initializeConnectionMonitor();
        initializeOpMonitor();

        SvInstance.registerWatcher(
            () => this.getConfigChangeListeners(),
            () => { this.onConfigChanged(); },
            {deep: true}
        );
    }

    showHeatmap(type, resetOnSwitch=true) {
        // Reset data if type was switched (and desired)

        if(type !== this.heatmapType && resetOnSwitch) {
            this.heatmapData = null;

            for(let op of SvInstance.pipeline.operators) op.monitor.heatmapRating = 0;
        }

        this.heatmapType = type;
    }

    isHeatmapActive() {
        return this.heatmapType > 0;
    }

    // ----------------------------------------------- Backend Reactivity ----------------------------------------------

    onConfigChanged() {
        if (SvInstance.pipeline.isPipelineStarted()) Services.Network.changeMonitorConfig(this.getConfig());
    }

    getConfigChangeListeners() {
        // Defines reactive config values to listen for changes and call onConfigChanged
        return [this.enabled, this.trackStats, this.heatmapType];
    }

    // -----------------------------------------------------------------------------------------------------------------

    getConfig() {
        return {
            "enabled": this.enabled,
            "trackStats": this.trackStats,
            "heatmapType": this.heatmapType,
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

export const HEATMAP  = {
    NONE: 0,
    COMPILE: 1,
    DATA_SIZE: 2,
    EXECUTION_TIME: 3,
}
