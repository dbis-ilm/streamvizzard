<template>
  <div>
    <div v-if="$streamvizzard.compiler.analyzed && operator.compiler.specs != null && operator.compiler.config != null">
      <div class="noSelect sectionHeader">Compile Target Settings</div>

      <SwitchSelection @input="_onModeChanged" v-model="config.manual" :class="[($streamvizzard.compiler.loading || specs.metaData.inheritTarget) && 'disabled']" :optionData="[
          {'value': false, 'label': 'Auto', 'title': 'Automatically infers the optimal configuration in the analysis'},
          {'value': true, 'label': 'Manual', 'title': 'User-defined configuration which will be considered by the analysis'}]"></SwitchSelection>

      <div :class="[($streamvizzard.compiler.loading || !config.manual) && 'disabled noSelect']">
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
          <input type="text" class="formInputField alignLeft" v-model="config.parallelismCount" @change="_onParallelismCountChanged"/>
        </div>

        <div v-if="specs.metaData.inheritTarget" style="padding-top:10px;"><i>Targets inherited from parents.</i></div>
      </div>

      <div :class="[$streamvizzard.compiler.loading && 'disabled noSelect']">
        <div class="formInputContainer" v-if="specs.metaData.canRestoreOutOfOrder" title="The tuple processing order can be restored by reordering at the expense of execution performance." style="margin-top: 2px;">
          <span class="formInputLabel limitedText alignLeft">Order Tuples:&nbsp;</span>
          <input type="checkbox" class="configCheckbox" v-model="config.enforceTupleOrder" @change="_onEnforceOrderChanged"/>
          <div style="margin-top: 0.5rem; text-align: center; width: 100%;">
            <span v-if="specs.metaData.outOfOrderProcessing" :title="outOfOrderCauseDescription" style="font-style: italic;">Out-Of-Order detected!</span>
          </div>
        </div>

        <div v-if="specs.metaData.outOfOrderProcessing && !specs.metaData.canRestoreOutOfOrder" style="padding-top:10px;" :title="outOfOrderCauseDescription">
          <i>Out-Of-Order detected!</i>
        </div>
      </div>

      <div class="targetStats" title="Desired execution stats for the operator of the selected compilation target.">
        <CollapseHeader :openedDir="'up'" class="sectionHeader" v-model="$streamvizzard.compiler.showStats" :title="'Requested Statistics'"></CollapseHeader>

        <CompileTargetStats v-show="$streamvizzard.compiler.showStats" :targetStats="config.targetStats"
                            :class="[$streamvizzard.compiler.loading && 'disabled noSelect']" @change="_onConfigChanged"/>
      </div>

      <div class="targetStats" title="Estimated execution stats for the operator of the selected compilation target.">
        <CollapseHeader :openedDir="'up'" class="sectionHeader" v-model="$streamvizzard.compiler.showEstStats" :title="'Estimated Statistics'"></CollapseHeader>

        <div v-show="$streamvizzard.compiler.showEstStats">
          <div class="formInputContainer">
            <span class="formInputLabel limitedText alignLeft" title="The estimated throughput of the operator">Throughput:&nbsp;</span>
            <FormInputWithUnit class="disabled" :type="'text'" :readonly="true" :value="specs.estExStats.estOutTp" :unit="'tuples / s'" :unitWidth="'80px'"></FormInputWithUnit>
          </div>
          <div class="formInputContainer">
            <span class="formInputLabel limitedText alignLeft" title="The estimated data transfer and communication time per tuple">Transfer Cost:&nbsp;</span>
            <FormInputWithUnit class="disabled" :type="'text'" :readonly="true" :value="specs.estExStats.estTransferTime" :unit="'ms'" :unitWidth="'35px'"></FormInputWithUnit>
          </div>
          <div class="formInputContainer">
            <span class="formInputLabel limitedText alignLeft" title="The estimated output data size of the operator">Output Size:&nbsp;</span>
            <FormInputWithUnit class="disabled" :type="'text'" :readonly="true" :value="specs.estExStats.outDataSize" :unit="'KByte'" :unitWidth="'55px'"></FormInputWithUnit>
          </div>
        </div>
      </div>

      <div class="clusterConnections" v-if="config.cluster != null && Object.keys(config.cluster.ccs).length > 0">
        <CollapseHeader :openedDir="'up'" class="sectionHeader" v-model="$streamvizzard.compiler.showCCs" :title="'Framework Connections'"></CollapseHeader>

        <ClusterConnection v-show="$streamvizzard.compiler.showCCs" :class="['clusterConnectionParams', $streamvizzard.compiler.loading && 'disabled noSelect']"
                           v-for="(cc, conID) in config.cluster.ccs" :key="operator.id + '_' + conID" :connectorCfg="cc"
                           :options="specs.clusterConOptions[conID]" :operator="operator"/>
      </div>

    </div>
    <div v-if="!$streamvizzard.compiler.analyzed">Compile settings are available after analyzing the pipeline!</div>
  </div>
</template>

<script>

import SwitchSelection from "@/components/interface/elements/base/SwitchSelection.vue";
import ClusterConnection from "@/components/features/compiler/ClusterConnection.vue";
import CompileTargetStats from "@/components/features/compiler/CompileTargetStats.vue";
import CollapseHeader from "@/components/interface/elements/base/CollapseHeader.vue";

import FormInputWithUnit from "@/components/interface/elements/base/FormInputWithUnit.vue";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";

export default {
  components: {FormInputWithUnit, CollapseHeader, CompileTargetStats, ClusterConnection, SwitchSelection},
  props: {
    operator: {type: SvOperator, required: true},
  },

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
    }
  },

  computed: {
    /** @return {OpCompileCfg} **/
    config() {
      return this.operator.compiler.config;
    },

    /** @return {OpCompileSpecs} **/
    specs() {
      return this.operator.compiler.specs;
    },

    outOfOrderCauseDescription() {
      if(this.specs.metaData.outOfOrderCause === "Join")
        return "Input values might be joined out-of-order! Resolve: Either ensure the same level of parallelism for all inputs and the join operator or select parallelism=1 for the join operator and activate the reordering of the data tuples.";
      else if(this.specs.metaData.outOfOrderCause === "Source")
        return "Values might be produced out-of-order! Resolve: use parallelism=1 to ensure a fixed data ingestion order."
      else if(this.specs.metaData.outOfOrderCause === "Window")
        return "Values might be collected out-of-order within the window partitions. Resolve: Ensure a parallelism=1 for the window operator or the same level of parallelism for all preceding operators."
      else if(this.specs.metaData.outOfOrderCause === "InputPara")
        return "Values might be processed out-of-order due to a redistribution from a higher level of parallelism (input operator) to the current operator. Resolve: Either ensure the same level of parallelism as the input operator or activate the reordering of the data tuples."
      else
        return "Values might be processed out-of-order!"
    },
  },

  watch: {
    config() {
      // Watch computed property to get notified when data (or op) changed
      this._buildCompileConfig();
    }
  },

  methods: {
    _buildCompileConfig() {
      if(this.operator.compiler.specs == null || this.config == null) return;

      this._buildFrameworks(this.operator.compiler.specs.frameworks);
    },

    /** @param {Array<OpCompileTargetFramework>} frameworks **/
    _buildFrameworks(frameworks) {
      this.frameworkOptions = [];
      this.frameworkSelected = null;

      let languageData = null;

      for(let framework of frameworks) {
        let envKey = framework.key;

        this.frameworkOptions.push({"key": envKey, "title": envKey});

        // Take first framework or selected one
        if (this.frameworkSelected == null || envKey === this.config.framework) {
          this.frameworkSelected = this.frameworkOptions[this.frameworkOptions.length - 1];
          languageData = framework.languages;
        }
      }

      this.config.framework = this.frameworkSelected["key"]; // Update config

      this._buildLanguages(languageData);
    },

    /** @param {Array<OpCompileTargetLanguage>} languages **/
    _buildLanguages(languages) {
      this.languageOptions = [];
      this.languageSelected = null;

      let computeModeData = null;

      for(let language of languages) {
        let languageKey = language.key;

        this.languageOptions.push({"key": languageKey, "title": languageKey});

        // Take first language or selected one
        if(this.languageSelected == null || languageKey === this.config.language) {
          this.languageSelected = this.languageOptions[this.languageOptions.length - 1];
          computeModeData = language.computeModes;
        }
      }

      this.config.language = this.languageSelected["key"]; // Update config

      this._buildComputeModes(computeModeData);
    },

    /** @param {Array<OpCompileTargetComputeMode>} computeModes **/
    _buildComputeModes(computeModes) {
      this.computeModeOptions = [];
      this.computeModeSelected = null;

      let parallelismData = null;

      for(let computeMode of computeModes) {
        let computeModeKey = computeMode.key;

        this.computeModeOptions.push({"key": computeModeKey, "title": computeModeKey});

        // Take first CM or selected one
        if(this.computeModeSelected == null || computeModeKey === this.config.computeMode) {
          this.computeModeSelected = this.computeModeOptions[this.computeModeOptions.length - 1];
          parallelismData = computeMode.parallelism;
        }
      }

      this.config.computeMode = this.computeModeSelected["key"]; // Update config

      this._buildParallelism(parallelismData);
    },

    /** @param {Array<String>} parallelisms **/
    _buildParallelism(parallelisms) {
      this.parallelismOptions = [];
      this.parallelismSelected = null;

      for(let parallelism of parallelisms) {
        this.parallelismOptions.push({"key": parallelism, "title": parallelism});

        // Take first parallelism or selected one
        if(this.parallelismSelected == null || parallelism === this.config.parallelism) {
          this.parallelismSelected = this.parallelismOptions[this.parallelismOptions.length - 1];
        }
      }

      this.config.parallelism = this.parallelismSelected["key"]; // Update config
    },

    _onTargetChanged() {
      this.config.manual = true;

      this.config.framework = this.frameworkSelected["key"];
      this.config.language = this.languageSelected["key"];
      this.config.computeMode = this.computeModeSelected["key"];
      this.config.parallelism = this.parallelismSelected["key"];

      this._buildCompileConfig();

      this._onConfigChanged();
    },

    _onModeChanged(event) {
      this.config.manual = event;

      if(!this.config.manual) this._onConfigChanged(); // Switched to auto
    },

    _onFrameworkSelected(event) {
      this.frameworkSelected = event;

      this._onTargetChanged();
    },

    _onLanguageSelected(event) {
      this.languageSelected = event;

      this._onTargetChanged();
    },

    _onComputeModeSelected(event) {
      this.computeModeSelected = event;

      this._onTargetChanged();
    },

    _onParallelismSelected(event) {
      this.parallelismSelected = event;

      if(event.key.toLowerCase() === 'distributed') this.config.parallelismCount = Math.max(this.config.parallelismCount, 2);
      else this.config.parallelismCount = 1;

      this._onTargetChanged();
    },

    _onParallelismCountChanged() {
      this._onTargetChanged();
    },

    _onEnforceOrderChanged() {
      this._onConfigChanged();
    },

    _onConfigChanged() {
      if(this.$streamvizzard.compiler.autoAnalyze) this.$streamvizzard.compiler.analyzePipeline();
    },
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
  margin-top: 0.65rem;
  flex: 0 0 auto;
}

</style>
