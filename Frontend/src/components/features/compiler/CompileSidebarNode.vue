<template>
  <div v-if="supportsCompilation">
    <div class="noSelect sectionHeader">Compile Target Settings</div>

    <SwitchSelection @input="_onModeChanged" v-model="compileData.config.manual" :class="!compileData.busy && !compileData.meta.inheritTarget ? '' : 'disabled'" :optionData="[
        {'value': false, 'label': 'Auto', 'title': 'Automatically infers the optimal configuration in the analysis'},
        {'value': true, 'label': 'Manual', 'title': 'User-defined configuration which will be considered by the analysis'}]"></SwitchSelection>

    <div :class="compileData.config.manual && !compileData.busy ? '' : 'disabled noSelect'">
      <div class="formInputContainer">
        <span class="formInputLabel limitedText alignLeft" title="Runtime environment to execute this operator">Framework:&nbsp;</span>
        <v-select v-auto-blur :clearable="false" :searchable="false" :options="frameworkOptions" class="formInputField" :value="frameworkSelected" @input="_onFrameworkSelected($event)" label="title"></v-select>
      </div>

      <div class="formInputContainer">
        <span class="formInputLabel limitedText alignLeft" title="Programming language to execute the operator">Language:&nbsp;</span>
        <v-select v-auto-blur :clearable="false" :searchable="false" :options="languageOptions" class="formInputField" :value="languageSelected" @input="_onLanguageSelected($event)" label="title"></v-select>
      </div>

      <div class="formInputContainer">
        <span class="formInputLabel limitedText alignLeft" title="Target infrastructure to execute the operator">Compute:&nbsp;</span>
        <v-select v-auto-blur :clearable="false" :searchable="false" :options="computeModeOptions" class="formInputField" :value="computeModeSelected" @input="_onComputeModeSelected($event)" label="title"></v-select>
      </div>

      <div class="formInputContainer">
        <span class="formInputLabel limitedText alignLeft" title="Mode to execute the operator">Parallelism:&nbsp;</span>
        <v-select v-auto-blur :clearable="false" :searchable="false" :options="parallelismOptions" class="formInputField" :value="parallelismSelected" @input="_onParallelismSelected($event)" label="title"></v-select>
      </div>

      <div class="formInputContainer" v-if="parallelismSelected != null && parallelismSelected.key.toLowerCase() === 'distributed'">
        <span class="formInputLabel limitedText alignLeft" title="The amount of parallelism for the execution">Executors:&nbsp;</span>
        <input type="text" class="formInputField alignLeft" v-model="parallelismCount" @change="_onParallelismCountChanged"/>
      </div>

      <div v-if="compileData.meta.inheritTarget" style="padding-top:10px;"><i>Targets inherited from parents.</i></div>
    </div>

    <div class="formInputContainer" v-if="compileData.meta.canRestoreOutOfOrder" title="The tuple processing order can be restored by reordering at the expense of execution performance." style="margin-top: 2px;">
      <span class="formInputLabel limitedText alignLeft">Order Tuples:&nbsp;</span>
      <input type="checkbox" class="configCheckbox" v-model="enforceTupleOrder" @change="_onEnforceOrderChanged"/>
      <div style="margin-top: 0.5rem; text-align: center; width: 100%;">
        <span v-if="compileData.meta.outOfOrderProcessing" :title="outOfOrderCauseDescription" style="font-style: italic;">Out-Of-Order detected!</span>
      </div>
    </div>

    <div v-if="compileData.meta.outOfOrderProcessing && !compileData.meta.canRestoreOutOfOrder" style="padding-top:10px;" :title="outOfOrderCauseDescription">
      <i>Out-Of-Order detected!</i>
    </div>

    <div class="targetStats" title="Desired execution stats for the operator of the selected compilation target.">
      <CollapseHeader :openedDir="'up'" class="sectionHeader" v-model="globalOpenStatsSection.value" :title="'Requested Statistics'"></CollapseHeader>

      <CompileTargetStats v-show="globalOpenStatsSection.value" :node="node" :targetStats="compileData.config.targetStats"></CompileTargetStats>
    </div>

    <div class="targetStats" title="Estimated execution stats for the operator of the selected compilation target.">
      <CollapseHeader :openedDir="'up'" class="sectionHeader" v-model="globalOpenEstStatsSection.value" :title="'Estimated Statistics'"></CollapseHeader>

      <div v-show="globalOpenEstStatsSection.value">
        <div class="formInputContainer">
          <span class="formInputLabel limitedText alignLeft" title="The estimated throughput of the operator">Throughput:&nbsp;</span>
          <FormInputWithUnit class="disabled" :type="'text'" :readonly="true" :value="compileData.targetStatsEstimation['estOutTp']" :unit="'tuples / s'" :unitWidth="'80px'"></FormInputWithUnit>
        </div>
        <div class="formInputContainer">
          <span class="formInputLabel limitedText alignLeft" title="The estimated data transfer and communication time per tuple">Transfer Cost:&nbsp;</span>
          <FormInputWithUnit class="disabled" :type="'text'" :readonly="true" :value="compileData.targetStatsEstimation['estTransferTime']" :unit="'ms'" :unitWidth="'35px'"></FormInputWithUnit>
        </div>
        <div class="formInputContainer">
          <span class="formInputLabel limitedText alignLeft" title="The estimated output data size of the operator">Output Size:&nbsp;</span>
          <FormInputWithUnit class="disabled" :type="'text'" :readonly="true" :value="compileData.targetStatsEstimation['outDataSize']" :unit="'KByte'" :unitWidth="'55px'"></FormInputWithUnit>
        </div>
      </div>
    </div>

    <div class="clusterConnections" v-if="compileData.config.cluster != null && Object.keys(compileData.config.cluster.ccs).length > 0">
      <CollapseHeader :openedDir="'up'" class="sectionHeader" v-model="globalOpenCCSection.value" :title="'Framework Connections'"></CollapseHeader>

      <ClusterConnection v-show="globalOpenCCSection.value" class="clusterConnectionParams" v-for="(cc, conID) in compileData.config.cluster.ccs"
                         :key="node.id + '_' + conID" :connectorCfg="cc" :options="compileData.clusterConnections[conID]" :node="node"/>
    </div>

  </div>
</template>

<script>

import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import SwitchSelection from "@/components/interface/elements/base/SwitchSelection.vue";
import ClusterConnection from "@/components/features/compiler/ClusterConnection.vue";
import CompileTargetStats from "@/components/features/compiler/CompileTargetStats.vue";
import CollapseHeader from "@/components/interface/elements/base/CollapseHeader.vue";

import Vue from "vue";
import FormInputWithUnit from "@/components/interface/elements/base/FormInputWithUnit.vue";

// Persistent even if we do not have op sidebar visible
let globalOpenCCSection = Vue.observable({value: true});
let globalOpenStatsSection = Vue.observable({value: true});
let globalOpenEstStatsSection = Vue.observable({value: true});

export default {
  name: 'CompileSidebarNode',
  components: {FormInputWithUnit, CollapseHeader, CompileTargetStats, ClusterConnection, SwitchSelection},
  props: ["node"],

  data() {
    return {
      frameworkOptions: [],
      frameworkSelected: null,

      languageOptions: [],
      languageSelected: null,

      computeModeOptions: [],
      computeModeSelected: null,

      parallelismOptions: [],
      parallelismSelected: null,

      parallelismCount: 1,

      enforceTupleOrder: true,

      globalOpenCCSection,
      globalOpenStatsSection,
      globalOpenEstStatsSection
    }
  },

  computed: {
    compileData() {
      return this.node.compileData;
    },

    supportsCompilation() {
      return this.compileData != null && this.compileData["config"] != null;
    },

    outOfOrderCauseDescription() {
      if(this.compileData.meta.outOfOrderCause === "Join")
        return "Input values might be joined out-of-order! Resolve: Either ensure the same level of parallelism for all inputs and the join operator or select parallelism=1 for the join operator and activate the reordering of the data tuples.";
      else if(this.compileData.meta.outOfOrderCause === "Source")
        return "Values might be produced out-of-order! Resolve: use parallelism=1 to ensure a fixed data ingestion order."
      else if(this.compileData.meta.outOfOrderCause === "Window")
        return "Values might be collected out-of-order within the window partitions. Resolve: Ensure a parallelism=1 for the window operator or the same level of parallelism for all preceding operators."
      else if(this.compileData.meta.outOfOrderCause === "InputPara")
        return "Values might be processed out-of-order due to a redistribution from a higher level of parallelism (input operator) to the current operator. Resolve: Either ensure the same level of parallelism as the input operator or activate the reordering of the data tuples."
      else
        return "Values might be processed out-of-order!"
    }
  },

  watch: {
    compileData() {
      // Watch computed property to get notified when data changed
      this._buildCompileConfig();
    }
  },

  methods: {
    _buildCompileConfig() {
      if(!this.supportsCompilation) return;

      this._buildFrameworks(this.compileData["frameworks"], this.compileData["config"]);

      this.enforceTupleOrder = this.compileData["config"]["enforceTupleOrder"];
    },

    _buildFrameworks(frameworks, config) {
      this.frameworkOptions = [];
      this.frameworkSelected = null;

      let languageData = null;

      for(let framework of frameworks) {
        let envKey = framework["key"];

        this.frameworkOptions.push({"key": envKey, "title": envKey});

        // Take first framework or selected one
        if (this.frameworkSelected == null || envKey === config["framework"]) {
          this.frameworkSelected = this.frameworkOptions[this.frameworkOptions.length - 1];
          languageData = framework["languages"];
        }
      }

      this.node.compileData["config"]["framework"] = this.frameworkSelected["key"]; // Update config

      this._buildLanguages(languageData, config);
    },

    _buildLanguages(languageData, config) {
      this.languageOptions = [];
      this.languageSelected = null;

      let computeModeData = null;

      for(let language of languageData) {
        let languageKey = language["key"];

        this.languageOptions.push({"key": languageKey, "title": languageKey});

        // Take first language or selected one
        if(this.languageSelected == null || languageKey === config["language"]) {
          this.languageSelected = this.languageOptions[this.languageOptions.length - 1];
          computeModeData = language["computeModes"];
        }
      }

      this.node.compileData["config"]["language"] = this.languageSelected["key"]; // Update config

      this._buildComputeModes(computeModeData, config);
    },

    _buildComputeModes(computeModeData, config) {
      this.computeModeOptions = [];
      this.computeModeSelected = null;

      let parallelismData = null;

      for(let computeMode of computeModeData) {
        let computeModeKey = computeMode["key"];

        this.computeModeOptions.push({"key": computeModeKey, "title": computeModeKey});

        // Take first CM or selected one
        if(this.computeModeSelected == null || computeModeKey === config["computeMode"]) {
          this.computeModeSelected = this.computeModeOptions[this.computeModeOptions.length - 1];
          parallelismData = computeMode["parallelism"];
        }
      }

      this.node.compileData["config"]["computeMode"] = this.computeModeSelected["key"]; // Update config

      this._buildParallelism(parallelismData, config);
    },

    _buildParallelism(parallelismData, config) {
      this.parallelismOptions = [];
      this.parallelismSelected = null;

      this.parallelismCount = config["parallelismCount"];

      for(let parallelism of parallelismData) {
        this.parallelismOptions.push({"key": parallelism, "title": parallelism});

        // Take first parallelism or selected one
        if(this.parallelismSelected == null || parallelism === config["parallelism"]) {
          this.parallelismSelected = this.parallelismOptions[this.parallelismOptions.length - 1];
        }
      }

      this.node.compileData["config"]["parallelism"] = this.parallelismSelected["key"]; // Update config
    },

    _onConfigurationChanged(manualMode = true) {
      this.node.compileData["config"]["manual"] = manualMode;

      this.node.compileData["config"]["framework"] = this.frameworkSelected["key"];
      this.node.compileData["config"]["language"] = this.languageSelected["key"];
      this.node.compileData["config"]["computeMode"] = this.computeModeSelected["key"];
      this.node.compileData["config"]["parallelism"] = this.parallelismSelected["key"];
      this.node.compileData["config"]["parallelismCount"] = this.parallelismCount;

      this._buildCompileConfig();

      executeEvent(EVENTS.COMPILE_CONF_CHANGED, this.node);
    },

    _onModeChanged(event) {
      if(!event) this._onConfigurationChanged(false); // Switched to auto
    },

    _onFrameworkSelected(event) {
      this.frameworkSelected = event;

      this._onConfigurationChanged();
    },

    _onLanguageSelected(event) {
      this.languageSelected = event;

      this._onConfigurationChanged();
    },

    _onComputeModeSelected(event) {
      this.computeModeSelected = event;

      this._onConfigurationChanged();
    },

    _onParallelismSelected(event) {
      this.parallelismSelected = event;

      if(event.key.toLowerCase() === 'distributed') this.parallelismCount = Math.max(this.parallelismCount, 2);
      else this.parallelismCount = 1;

      this._onConfigurationChanged();
    },

    _onParallelismCountChanged(event) {
      this.parallelismCount = event.target.value;

      this._onConfigurationChanged();
    },

    _onEnforceOrderChanged(event) {
      this.enforceTupleOrder = event.target.checked;

      this.node.compileData["config"]["enforceTupleOrder"] = this.enforceTupleOrder;

      // Keep manual/auto mode
      this._onConfigurationChanged(this.node.compileData["config"]["manual"]);
    }
  },

  mounted() {
    this._buildCompileConfig();
  }
}

</script>

<style scoped>

.formInputLabel {
  width: 110px;
}

.clusterConnections, .targetStats {
  margin-top: 15px;
}

.clusterConnectionParams {
  margin-top: 10px;
}

hr {
  color: var(--main-border-color);
}

.sectionHeader {
  text-decoration: underline;
  font-weight: bold;
}

.configCheckbox {
  margin-top: 0.75rem;
  display:block;
  height: 1rem;
  width: 1rem;
}

</style>
