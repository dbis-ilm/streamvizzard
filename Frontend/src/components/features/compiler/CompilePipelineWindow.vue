<template>
  <div id="compilePipelineWindow" class="window" v-if="opened">
    <div class="windowContent" :class="(loading ? ' loading' : '')">
      <div class="windowTitle">Compile Pipeline</div>

      <SwitchSelection v-model="optionsMode" :optionData="[
        {'value': 'placement', 'label': 'Placement'},
        {'value': 'compile', 'label': 'Compile'}]"></SwitchSelection>

      <CompileStrategySelect v-show="optionsMode === 'placement'" class="optionSelect" ref="placementStrategySelect"
                             :strategyOptions="placementStrategyOptions"></CompileStrategySelect>

      <CompileStrategySelect v-show="optionsMode === 'compile'" class="optionSelect" ref="compileStrategySelect"
                             :strategyOptions="compileStrategyOptions" :toggleSettings="false" :showStrategySelect="false"></CompileStrategySelect>

      <div v-if="errorMessage != null" class="errorMsg" v-html="errorMessage"/>
      <div v-if="successMessage != null" class="successMsg" v-html="successMessage"/>

      <div class="modalFooterButtons">
        <ButtonSec :label="'Cancel'" @click="hide"/>
        <ButtonSec :class="connectionError ? 'disabled' : ''" :label="'Analyze'" @click="_analyze"/>
        <ButtonSec :label="'Compile'" :class="!connectionError && canCompile ? '' : 'disabled'" @click="_compile"/>
      </div>
    </div>
  </div>
</template>

<script>

//TODO: We could also provide further heatmaps to view computeMode / language / parallelisms...

import ButtonSec from "@/components/interface/elements/base/ButtonSec.vue";
import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import {system} from "@/main";
import {NetworkService} from "@/scripts/services/network/NetworkService";
import {safeVal} from "@/scripts/tools/Utils";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";
import CompileStrategySelect from "@/components/features/compiler/CompileStrategySelect.vue";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";
import {
  CompileOptionCheckbox, CompileOptionGrouper,
  CompileOptionStrategy, CompileOptionTextInput, CompileOptionTextInputUnit, getDefaultPlacementStrategy,
  matchOtherClusterSideConType
} from "@/scripts/components/compiler/CompileUtils";
import SwitchSelection from "@/components/interface/elements/base/SwitchSelection.vue";

let sharedTransferPenalties = [
  new CompileOptionTextInputUnit("avgNodeTransferSpeed", "Node Speed", "The data rate for inter-node communication.", "100", "100", "MB/s", "50px"),
  new CompileOptionTextInputUnit("avgNodeTransferLatency", "Node Latency", "The latency for inter-node communication.", "0.25", "0.25", "ms", "35px"),
  new CompileOptionTextInputUnit("avgConnectorTransferSpeed", "Conn. Speed", "The data rate for connector communication.", "100", "100", "MB/s", "50px"),
  new CompileOptionTextInputUnit("avgConnectorTransferLatency", "Conn. Latency", "The latency for connector communication.", "10", "10", "ms", "35px")
];

let sharedGeneral = [
  new CompileOptionTextInput("maxNodesCount", "Max Executors", "How many processing nodes are available in total for the final execution.", "Unlimited", "10"),
  new CompileOptionTextInput("costModelPath", "Cost Models", "The path for the costModels to consider during calculation.", "/Path/To/Folder")
];

let sharedPlacementOptions = [
  new CompileOptionGrouper("Data Transfer Rates", "Defines various data transfer rates an latency for the pipeline.", sharedTransferPenalties),
  new CompileOptionGrouper("General", "General placement options", sharedGeneral)
];

export default {
  name: 'CompilePipelineWindow',
  components: {SwitchSelection, CompileStrategySelect, ButtonSec},

  data() {
    return {
      opened: false,
      loading: false,
      errorMessage: null,
      successMessage: null,

      connectionError: false,
      canCompile: false,

      optionsMode: "placement",

      placementStrategyOptions: [getDefaultPlacementStrategy(sharedPlacementOptions)],

      compileStrategyOptions: [
        new CompileOptionStrategy("default", "Default", [new CompileOptionCheckbox("mergeCluster", "Merge Cluster", "Merges sub-pipelines of same frameworks together, if possible.", true)]),
      ],

      saveData: null, // Save data to be stored into or loaded from safe file
    }
  },

  methods: {
    show () {
      if(this.opened) return;

      this.opened = true;

      this._reset();

      system.compileMode = true;

      this.$nextTick(() => this._restoreSaveData());

      let data = {"pipeline": PipelineService.createPipelineData()};

      this.loading = true;

      let ths = this;
      NetworkService.startCompileMode(data).then((res) => {
        ths.loading = false;

        if(res == null) ths.errorMessage = "Couldn't connect to the server!";
        else if(res["res"] === false) ths.errorMessage = "Couldn't start compile mode:<br><i>" + res["error"] + "</i>";

        ths.connectionError = res == null;
      });
    },

    hide () {
      if(!this.opened) return;

      this.opened = false;

      // Keep config data for storing into safe file
      this.saveData = this._getSaveData();

      this._reset();

      system.$refs.heatmap.hide();

      system.compileMode = false;
      NetworkService.endCompileMode();
    },

    _reset() {
      this.canCompile = false;
      this.errorMessage = null;
      this.connectionError = false;
      this.successMessage = null;
      this.loading = false;

      for(let v of PipelineService.getAllOperators()) {
        if(v.compileData != null) {
          this.$set(v, "compileData", null); // Update reactivity
        }

        v.component.setHeatmapRating(v, 0);
        v.component.reset(v, true, false);
      }
    },

    _analyze() {
      if(this.loading) return;

      let data = {};

      data["strategy"] = this.$refs.placementStrategySelect.getStrategyData();
      data["compileConfigs"] = this._collectConfigs();

      this.errorMessage = null;
      this.successMessage = null;
      this.canCompile = false;

      this._setLoading(true);

      let ths = this;

      NetworkService.compileAnalyze(data).then((res) => {
        if(res == null || res === false) {
          ths._setLoading(false);
          ths.errorMessage = "Couldn't analyze pipeline!";

          return;
        }

        let missingExStats = false;

        for(let r of res["opData"]) {
          let op = PipelineService.getOperatorByID(r["opID"]);

          if(op === null) continue;

          ths.$set(op, "compileData", r["res"]); // Add reactivity to new property

          if(!r["status"]?.["exStatsAvail"]) missingExStats = true;
        }

        // If we have previous config data, try to apply it to new compile data
        // This ensures that we get the same cluster connection params as in safe file

        for(let op of PipelineService.getAllOperators()) {
          let prevCfg = this.saveData?.["configs"]?.[op.id];
          if(prevCfg != null) this._tryApplySaveCCData(op.id, prevCfg, op.compileData);
        }

        ths._visualizeCluster();

        ths.canCompile = res["canCompile"];
        ths.errorMessage = res["error"];

        if(missingExStats) ths.errorMessage = (ths.errorMessage != null ? ths.errorMessage + "<br>" : "")
            + "<span class='warningMsg' title='To improve the quality of the compilation process, first execute the pipeline with activated \"Settings/Monitor/Track Stats\" to gather execution stats!'>ExecutionStats missing for some operators!</span>";

        if(res["statusMsg"]) ths.successMessage = res["statusMsg"];
        ths._setLoading(false);
      });
    },

    _visualizeCluster() {
      let clusterIDs = new Map();

      for(let v of PipelineService.getAllOperators()) {
        if(safeVal(v.compileData) == null || v.compileData.config == null) continue;

        let clusterData = v.compileData.config.cluster;

        if(clusterData == null) continue;

        if(!clusterIDs.has(clusterData["id"])) clusterIDs.set(clusterData["id"], clusterIDs.size);
      }

      for(let v of PipelineService.getAllOperators()) {
        if(safeVal(v.compileData) == null || v.compileData.config == null) continue;

        let clusterData = v.compileData.config.cluster;

        let rating = 0;

        if(clusterData != null) rating = clusterIDs.get(clusterData["id"]) / clusterIDs.size;

        v.component.setHeatmapRating(v, rating);
      }

      system.$refs.heatmap.show(0);
    },

    _onUserConfigChanged() {
      this._analyze(); // Reanalyze
    },

    _setLoading(loading) {
      this.loading = loading;

      for(let v of PipelineService.getAllOperators()) {
        let compileData = v.compileData;
        if(compileData != null) compileData.busy = loading;
      }
    },

    _compile() {
      if(!this.canCompile || this.loading) return;

      this.errorMessage = null;
      this.successMessage = null;

      this._setLoading(true);

      let ths = this;

      let data = {"opCompileConfigs": this._collectConfigs(), "compileConfig": this.$refs.compileStrategySelect.getStrategyData()};

      NetworkService.compilePipeline(data).then((res) => {
        ths._setLoading(false);

        if(res == null) ths.errorMessage = "Couldn't compile the pipeline!";
        else ths.errorMessage = res["errorMsg"];

        // statusMsg contains output path of compiled files
        if(res["success"]) ths.successMessage = "Compilation successful!<br><div class='compileGenResPath limitedText' title='" + res['statusMsg'] + "'>" + res['statusMsg'] + "</div>"
      });
    },

    _tryApplySaveCCData(opID, prevConf, newData) {
      if(prevConf == null) return;

      function findMatchingCCOption(compileData, conID, conType) {
        // Finds the matching connector config for the connection and connectorType

        let options = compileData["clusterConnections"][conID];

        if (options == null) return null;

        // Get matching option for conType

        for (let option of options) {
          if (option["ourConType"] === conType) return option;
        }

        return null;
      }

      // Check for each new connection if we had a matching config for this

      for(let cID of Object.keys(newData["clusterConnections"])) {
        let conID = parseInt(cID); // Keys are always strings coming from json ...

        let prevCConf = prevConf.cluster?.["ccs"][conID];

        if(prevCConf == null) continue;

        // Check if our config is still supported

        let matchingOption = findMatchingCCOption(newData, conID, prevCConf["conType"]);

        if(matchingOption == null) continue;

        let params = prevCConf["params"];

        // Verify that the keys of our config and the connector match

        if(!Object.keys(params).every((key) => key in matchingOption["ourConParams"])) continue
        if(!Object.keys(matchingOption["ourConParams"]).every((key) => key in params)) continue

        // Check if the other side has a matching connector and apply it for the other side in this case

        let res = matchOtherClusterSideConType(opID, conID, prevCConf["conType"], params);

        if(!res) continue;

        // Adapt our cfg (other side including params was adapted in matchOtherClusterSideConType call)

        let currentCfg = newData["config"]?.["cluster"]?.["ccs"]?.[conID];

        currentCfg["conType"] = prevCConf["conType"];
        currentCfg["params"] = params;
      }
    },

    _collectConfigs() {
      let compileConfigs = {};

      // Collect all configurations for the operators

      for(let v of PipelineService.getAllOperators()) {
        // Try load config from saveData if present
        let saveData = this.saveData?.["configs"]?.[v.id] ?? null;

        if(saveData != null) compileConfigs["" + v.id] = saveData;

        if(v.compileData?.config != null) compileConfigs["" + v.id] = v.compileData.config;
      }

      return compileConfigs;
    },

    _restoreSaveData() {
      if(this.saveData == null) return;

      let placementSettings = this.saveData["placementSettings"];
      this.$refs.placementStrategySelect.setStrategyData(placementSettings);

      let compileSettings = this.saveData["compileSettings"];
      this.$refs.compileStrategySelect.setStrategyData(compileSettings);
    },

    _loadSaveData(saveData) {
      this.saveData = saveData;
    },

    _getSaveData() {
      return {
        "configs": this._collectConfigs(),
        "placementSettings": this.$refs.placementStrategySelect.getStrategyData(),
        "compileSettings": this.$refs.compileStrategySelect.getStrategyData()
      };
    },
  },

  mounted() {
    registerEvent([EVENTS.PIPELINE_STATUS_CHANGED, EVENTS.CLEAR_PIPELINE, EVENTS.MODAL_OPENED, EVENTS.DISCONNECTED], this.hide);

    // Any changes to the pipelineState will cancel the compile mode
    registerEvent(EVENTS.PIPELINE_MODIFIED, this.hide);

    registerEvent(EVENTS.COMPILE_CONF_CHANGED, this._onUserConfigChanged);

    registerEvent(EVENTS.NODE_REPLACED, (newNode, oldNode) => {
      // When a node is replaced lookup the old saveData and copy it to the new ID
      if(this.saveData?.["configs"]) {
        this.saveData["configs"][newNode.id] = this.saveData["configs"]?.[oldNode.id];
      }
    });

    DataExportService.registerDataExporter("compiler", () => { return !this.opened ? this.saveData : this._getSaveData() }, this._loadSaveData);
  }
}
</script>

<style>

#compilePipelineWindow .compileGenResPath {
  font-style: italic;
  font-size: 0.75em;
  width: 100%;
  max-width: 100%;
}

</style>

<style scoped>

#compilePipelineWindow {
  position: absolute;
  left: 50%;
  transform: translate(-50%, 0);
  margin-top: -2px;
  border-top-left-radius: initial;
  border-top-right-radius: initial;
  width: 350px;
}

.optionSelect {
  margin-top: 10px;
}

.loading {
  pointer-events: none;
  opacity: 0.75;
}

</style>
