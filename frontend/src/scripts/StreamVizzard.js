import {Advisor} from "@/scripts/features/advisor/Advisor";
import Vue from "vue";
import {valueOr} from "@/scripts/tools/Utils";
import {Debugger} from "@/scripts/features/debugger/Debugger";
import {Monitor} from "@/scripts/features/monitor/Monitor";
import {Services} from "@/scripts/services/Services";
import {Pipeline} from "@/scripts/pipeline/Pipeline";
import {Modules} from "@/scripts/pipeline/operators/modules/Modules";
import Editor from "@/scripts/editor/Editor";
import Compiler from "@/scripts/features/compiler/Compiler";
import Interface from "@/scripts/interface/Interface";

/**
 * @class StreamVizzard
 */
export class StreamVizzard {
    constructor() {
        /** @type String **/
        this.version = "0.9.6";

        // Restore last pipeline after page refresh
        this.restorePipeline = valueOr(localStorage.getItem("restorePipeline"), "true") === "true"

        this.modules = new Modules();

        this.interface = new Interface();
        this.editor = new Editor();

        this.pipeline = new Pipeline();

        this.monitor = new Monitor();
        this.advisor = new Advisor();
        this.debugger = new Debugger();
        this.compiler = new Compiler();

        this._watcherHost = new Vue();
    }

    toggleRestorePipeline(restore) {
        this.restorePipeline = restore;

        localStorage.setItem("restorePipeline", this.restorePipeline);
    }

    getRuntimeConfig() {
        return {
            "pipeline": this.pipeline.getRuntimeConfig(),
            "monitor": this.monitor.getConfig(),
            "debugger": this.debugger.getConfig(),
            "advisor": this.advisor.getConfig(),
        };
    }

    // ---------------------------------------------------- System -----------------------------------------------------

    initializeSystem() {
        // Register data exporter

        Services.DataExporter.registerDataExporter("pipeline", // Must be first entry!
            () => { return this.pipeline.exportSaveData() },
            async(data) => { await this.pipeline.importSaveData(data) });

        Services.DataExporter.registerDataExporter("monitor",
            () => { return this.monitor.exportSaveData() },
            (data) => { this.monitor.importSaveData(data); });

        Services.DataExporter.registerDataExporter("advisor",
            () => { return this.advisor.exportSaveData() },
            (data) => { this.advisor.importSaveData(data); });

        Services.DataExporter.registerDataExporter("debugger",
            () => { return this.debugger.exportSaveData() },
            (data) => { this.debugger.importSaveData(data); });

        Services.DataExporter.registerDataExporter("compiler",
            () => { return this.compiler.exportSaveData() },
            (data) => { this.compiler.importSaveData(data); });

        Services.DataExporter.registerDataExporter("editor",
            () => { return this.editor.exportSaveData() },
            (data) => { this.editor.importSaveData(data); });

        Services.DataExporter.registerDataExporter("interface",
            () => { return this.interface.exportSaveData() },
            (data) => { this.interface.importSaveData(data); });

        this.modules.load();

        this.pipeline.initialize();
        this.monitor.initialize();
        this.debugger.initialize();
        this.compiler.initialize();
        this.editor.initialize();

        Services.initialize();
    }

    registerWatcher(exp, callback, options = {}) {
        this._watcherHost.$watch(exp, callback, options);
    }

    isDockerExecution() {
        return process.env.VUE_APP_DOCKER === 'true'
    }
}

/** @type {StreamVizzard} */
export const SvInstance = Vue.observable(new StreamVizzard());
