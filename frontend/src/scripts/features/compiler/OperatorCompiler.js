import Vue from "vue";
import {safeVal} from "@/scripts/tools/Utils";

export default class OperatorCompiler {
    /** @type {SvOperator} operator **/
    constructor(operator) {
        this.operator = operator;

        /** @type {OpCompileCfg|null} **/
        this.config = null;

        /** @type {OpCompileSpecs|null} **/
        this.specs = null;
    }

    loadData(data) {
        this.specs = new OpCompileSpecs(data);

        // Make config reactive for the UI
        if(safeVal(data["config"]) != null) this.config = new Vue.observable(new OpCompileCfg(data["config"]));
        else this.config = null;
    }

    reset() {
        this.specs = null; // Keep config for reloading
    }

    // ------------------------------------------------ Config / Storage -----------------------------------------------

    exportSaveData() {
        return {"config": this.config != null ? this.config : null};
    }

    importSaveData(data) {
        let cfgData = safeVal(data["config"]);
        if(cfgData != null) this.config = new Vue.observable(new OpCompileCfg(cfgData));
    }
}

// --------------------------------------------------- Compile Data ----------------------------------------------------

// Compile Specifications

class OpCompileSpecs {
    /** @type {Array<OpCompileTargetFramework>} **/ frameworks = [];
    /** @type OpCompileMetaData **/ metaData;
    /** @type OpCompileEstimatedStats **/ estExStats;
    /** @type {Object<Number, Array<OpCompileCCOption>>} **/ clusterConOptions = {};

    constructor(data) {
        // Frameworks

        for (let fwData of data["frameworks"])
            this.frameworks.push(new OpCompileTargetFramework(fwData));

        // Meta

        this.metaData = new OpCompileMetaData();
        Object.assign(this.metaData, data["meta"]);

        // Estimated Stats

        this.estExStats = new OpCompileEstimatedStats();
        Object.assign(this.estExStats, data["targetStatsEstimation"]);

        // CC Options

        for(let [conID, optionsData] of Object.entries(data["clusterConnections"])) {
            let ccOptions = [];

            for(let option of optionsData) {
                let op = new OpCompileCCOption();
                Object.assign(op, option);

                ccOptions.push(op);
            }

            this.clusterConOptions[conID] = ccOptions;
        }
    }
}

// ---

class OpCompileTargetFramework {
    /** @type String **/ key;
    /** @type {Array<OpCompileTargetLanguage>} **/ languages = [];

    constructor(fwData) {
        this.key = fwData["key"];

        for (let langData of fwData["languages"])
            this.languages.push(new OpCompileTargetLanguage(langData));
    }
}

class OpCompileTargetLanguage {
    /** @type String **/ key;
    /** @type {Array<OpCompileTargetComputeMode>} **/ computeModes = [];

    constructor(langData) {
        this.key = langData["key"];

        for (let cmData of langData["computeModes"])
            this.computeModes.push(new OpCompileTargetComputeMode(cmData));
    }
}

class OpCompileTargetComputeMode {
    /** @type String **/ key;
    /** @type {Array<String>} **/ parallelism;

    constructor(cmData) {
        this.key = cmData["key"];
        this.parallelism = cmData["parallelism"];
    }
}

// ---

class OpCompileMetaData {
    /** @type Boolean **/ inheritTarget;

    /** @type Boolean **/ canRestoreOutOfOrder;
    /** @type Boolean **/ outOfOrderProcessing;
    /** @type String **/ outOfOrderCause;
}

class OpCompileEstimatedStats {
    /** @type Number **/ estExTime;
    /** @type Number **/ estOutTp;
    /** @type Number **/ estTransferTime;
    /** @type Number **/ outDataSize;
}

// ---

export class OpCompileCCOption {
    /** @type String **/ ourConType;
    /** @type Object **/ ourConParams;
    /** @type String **/ otherConType;
}

// Compile Config

class OpCompileCfg {
    /** @type Boolean **/ manual;
    /** @type String **/ framework;
    /** @type String **/ language;
    /** @type String **/ computeMode;
    /** @type String **/ parallelism;
    /** @type Number **/ parallelismCount;
    /** @type Boolean **/ enforceTupleOrder;
    /** @type {OpCompileCfgCluster|null} **/ cluster;
    /** @type OpCompileCfgTargetStats **/ targetStats;

    constructor(cfgData) {
        Object.assign(this, cfgData);

        let stats = new OpCompileCfgTargetStats();
        Object.assign(stats, cfgData["targetStats"]);

        this.targetStats = stats;

        if(cfgData["cluster"] != null) {
            this.cluster = new OpCompileCfgCluster();
            this.cluster.loadData(cfgData["cluster"]);
        }
    }
}

class OpCompileCfgCluster {
    /** @type Number **/ id;
    /** @type {Object<Number, OpCompileCfgClusterCon>} **/ ccs = {};

    loadData(data) {
        this.id = data["id"];

        for(let cc of Object.values(data["ccs"])) {
            let con = new OpCompileCfgClusterCon();
            Object.assign(con, cc);
            this.ccs[cc["conID"]] = con;
        }
    }
}

export class OpCompileCfgClusterCon {
    /** @type Number **/ conID;
    /** @type String **/ conType;
    /** @type Object **/ params;
}

export class OpCompileCfgTargetStats {
    /** @type Boolean **/ autoTp;
    /** @type Number **/ targetTp;

    /** @type Boolean **/ autoExTime;
    /** @type Number **/ targetExTime;
    /** @type String **/ exTimeSource;
}
