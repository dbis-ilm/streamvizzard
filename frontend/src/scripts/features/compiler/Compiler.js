import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import {SvInstance} from "@/scripts/StreamVizzard";
import {Services} from "@/scripts/services/Services";
import {HEATMAP} from "@/scripts/features/monitor/Monitor";
import {safeVal} from "@/scripts/tools/Utils";
import {getStrategyByName} from "@/scripts/features/compiler/CompileStrategies";
import {matchOtherClusterSideConType} from "@/scripts/features/compiler/CompileUtils";

export default class Compiler {
    constructor() {
        this.enabled = false;

        this.initialized = false; // If compile mode was started by the backend
        this.analyzed = false; // If the pipeline was analyzed by the backend

        this.loading = false;
        this.canCompile = false;

        this.errorMessage = null;
        this.successMessage = null;

        // Placement/Compile Settings

        /** @type{CompileOptionStrategy|null} **/
        this.placementSettings = null;

        /** @type{CompileOptionStrategy|null} **/
        this.compileSettings = null;

        // UI Settings

        this.autoAnalyze = true;

        this.showCCs = true;
        this.showStats = true;
        this.showEstStats = true;
    }

    initialize() {
        // Any changes to the pipelineState will cancel the compile mode
        registerEvent([EVENTS.PIPELINE_STATUS_CHANGED, EVENTS.PIPELINE_CLEARED, EVENTS.MODAL_OPENED, EVENTS.DISCONNECTED, EVENTS.PIPELINE_MODIFIED],
            () => this.endCompileMode());
    }

    startCompileMode() {
        if(this.enabled) return;

        this.enabled = true;

        this._reset();

        // Establish server connection

        let data = {"pipeline": SvInstance.pipeline.getRuntimeConfig()};

        this.loading = true;

        Services.Network.startCompileMode(data).then((res) => {
            this.loading = false;

            if(res == null) this.errorMessage = "Couldn't connect to the server!";
            else if(res["res"] === false) this.errorMessage = "Couldn't start compile mode:<br><i>" + res["error"] + "</i>";

            this.initialized = res != null;
        });
    }

    endCompileMode() {
        if(!this.enabled) return;

        this.enabled = false;

        this._reset();

        SvInstance.monitor.showHeatmap(HEATMAP.NONE);

        Services.Network.endCompileMode();
    }

    analyzePipeline() {
        if(this.loading) return;

        let data = {};

        data["strategy"] = this.placementSettings.getStrategyData();
        data["compileConfigs"] = this._collectConfigs();

        this.errorMessage = null;
        this.successMessage = null;
        this.canCompile = false;

        this.loading = true;

        Services.Network.compileAnalyze(data).then((res) => {
            if(res == null || res === false) {
                this.loading = false;
                this.analyzed = false; // Only set to false again if analyze failed!
                this.errorMessage = "Couldn't analyze pipeline!";

                return;
            }

            let missingExStats = false;

            for(let r of res["opData"]) {
                let op = SvInstance.pipeline.getOperatorByID(r["opID"]);
                if(op === null) continue;

                op.compiler.loadData(r["res"]);

                if(!r["status"]?.["exStatsAvail"]) missingExStats = true;
            }

            // If we have previous (stored) config data, try to apply it to new compile data
            // This ensures that we get the same cluster connection params as in safe file

            let prevConfigs = data["compileConfigs"];

            for(let op of SvInstance.pipeline.operators) {
                let prevCfg = prevConfigs[op.id];
                if(prevCfg != null && op.compiler.config != null) this._tryApplySaveCCData(op.id, prevCfg, op.compiler.config, op.compiler.specs);
            }

            this._visualizeCluster();

            this.canCompile = res["canCompile"];
            this.analyzed = true;
            this.errorMessage = res["error"];

            if(missingExStats) this.errorMessage = (this.errorMessage != null ? this.errorMessage + "<br>" : "")
                + "<span class='warningMsg' title='To improve the quality of the compilation process, first execute the pipeline with activated \"Settings/Monitor/Track Stats\" to gather execution stats!'>ExecutionStats missing for some operators!</span>";

            if(res["statusMsg"]) this.successMessage = res["statusMsg"];
            this.loading = false;
        });
    }

    compilePipeline() {
        if(!this.canCompile || this.loading) return;

        this.errorMessage = null;
        this.successMessage = null;

        this.loading = true;

        let data = {"opCompileConfigs": this._collectConfigs(), "compileConfig": this.compileSettings.getStrategyData()};

        Services.Network.compilePipeline(data).then((res) => {
            this.loading = false;

            if(res == null) this.errorMessage = "Couldn't compile the pipeline!";
            else {
                this.errorMessage = res["errorMsg"];

                // statusMsg contains output path of compiled files
                if(res["success"]) this.successMessage = "Compilation successful!<br><div class='compileGenResPath limitedText' title='" + res['statusMsg'] + "'>" + res['statusMsg'] + "</div>";
            }
        });
    }

    isActive() {
        return this.enabled && this.analyzed;
    }

    _visualizeCluster() {
        let clusterIDs = new Map();

        for(let op of SvInstance.pipeline.operators) {
            if(op.compiler.config == null) continue;

            let clusterData = op.compiler.config.cluster;
            if(clusterData == null) continue; // Not part of cluster

            if(!clusterIDs.has(clusterData.id)) clusterIDs.set(clusterData.id, clusterIDs.size);
        }

        for(let op of SvInstance.pipeline.operators) {
            if(op.compiler.config == null) continue;

            let clusterData = op.compiler.config.cluster;

            let rating = 0;

            if(clusterData != null) rating = clusterIDs.get(clusterData.id) / clusterIDs.size;

            op.monitor.heatmapRating = rating;
        }

        SvInstance.monitor.showHeatmap(HEATMAP.COMPILE, false);
    }

    _collectConfigs() {
        let compileConfigs = {};

        // Collect all configurations for the operators

        for(let op of SvInstance.pipeline.operators) {
            if(op.compiler.config != null) compileConfigs["" + op.id] = op.compiler.config;
        }

        return compileConfigs;
    }

    /** @param {Number} opID
     * @param {OpCompileCfg} prevConf
     * @param {OpCompileCfg} newConf
     * @param {OpCompileSpecs} newSpecs **/
    _tryApplySaveCCData(opID, prevConf, newConf, newSpecs) {
        function findMatchingCCOption(conID, conType) {
            // Finds the matching connector config for the connection and connectorType

            let options = newSpecs.clusterConOptions[conID];
            if (options == null) return null;

            // Get matching option for conType

            for (let option of options) {
                if (option.ourConType === conType) return option;
            }

            return null;
        }

        // Check for each new connection if we had a matching config for this

        for(let cID of Object.keys(newSpecs.clusterConOptions)) {
            let conID = parseInt(cID); // Keys are always strings coming from json ...

            // Ensure old and new config belong to a cluster and have a cc for the same connection

            if(prevConf.cluster == null || newConf.cluster == null ||
                !(conID in prevConf.cluster.ccs) || !(conID in newConf.cluster.ccs)) continue;

            let prevCConf = prevConf.cluster.ccs[conID];
            let currentCCfg = newConf.cluster.ccs[conID];

            // Check if our config is still supported

            let matchingOption = findMatchingCCOption(conID, prevCConf.conType);
            if(matchingOption == null) continue;

            let params = prevCConf.params;

            // Verify that the keys of our config and the connector match

            if(!Object.keys(params).every((key) => key in matchingOption.ourConParams)) continue
            if(!Object.keys(matchingOption.ourConParams).every((key) => key in params)) continue

            // Check if the other side has a matching connector and apply it for the other side in this case

            if(!matchOtherClusterSideConType(opID, conID, prevCConf.conType, params)) continue;

            // Adapt our cfg (other side including params was adapted in matchOtherClusterSideConType call)

            currentCCfg.conType = prevCConf.conType;
            currentCCfg.params = params;
        }
    }

    _reset() {
        this.successMessage = null;
        this.errorMessage = null;
        this.initialized = false;
        this.loading = false;
        this.canCompile = false;
        this.analyzed = false;

        for(let op of SvInstance.pipeline.operators) {
            op.compiler.reset();
            op.resetState(true);
        }
    }

    // ------------------------------------------------ Config / Storage -----------------------------------------------

    exportSaveData() {
        return {
            "placementSettings": this.placementSettings != null ? this.placementSettings.getStrategyData() : null,
            "compileSettings": this.compileSettings != null ? this.compileSettings.getStrategyData() : null,
            "autoAnalyze": this.autoAnalyze,
            "showStats": this.showStats,
            "showCCs": this.showCCs,
            "showEstStats": this.showEstStats,
        };
    }

    importSaveData(data) {
        let placementStrat = safeVal(data["placementSettings"]);
        if(placementStrat != null) {
            this.placementSettings = getStrategyByName(placementStrat["name"], true);
            if(this.placementSettings != null) this.placementSettings.setData(placementStrat["settings"]);
        }

        let compileStrat = safeVal(data["compileSettings"]);
        if(compileStrat != null) {
            this.compileSettings = getStrategyByName(compileStrat["name"], false);
            if(this.compileSettings != null) this.compileSettings.setData(compileStrat["settings"]);
        }

        this.autoAnalyze = safeVal(data["autoAnalyze"], this.autoAnalyze);
        this.showStats = safeVal(data["showStats"], this.showStats);
        this.showCCs = safeVal(data["showCCs"], this.showCCs);
        this.showEstStats = safeVal(data["showEstStats"], this.showEstStats);
    }
}