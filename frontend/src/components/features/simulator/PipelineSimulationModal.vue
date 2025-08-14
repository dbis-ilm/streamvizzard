<template>
  <modal ref="modal" name="PipelineSimulationModal" transition="pop-out" :width="325" height="auto" :shiftY="0" :shiftX="0.075" style="top: 10%;">
    <div style="padding:10px;">
      <div style="text-decoration: underline;"><b>Simulate Pipeline</b></div>
      <br/>
      <div style="display:flex; flex-direction: row; height: 34px;">
        <div class="title limitedText" style="padding-top: 5px;">Duration:&nbsp;</div>
        <input class="content" title="How many seconds the simulation should calculate" type="number" v-model="duration">
      </div>
      <div style="display:flex; flex-direction: row; margin-top: 10px;">
        <span class="title v" style="padding-top: 5px;">Mode:&nbsp;</span>
        <v-select v-auto-blur class="content alignedSelect" :options="modeOptions" label="title" :value="mode" :clearable="false" :searchable="false" @input="_onChange($event)"></v-select>
      </div>
      <div class="inputElmContainer">
        <span class="title limitedText" title="Cost Model storage folder" style="padding-top: 5px;">CM Path:&nbsp;</span>
        <input type="text" class="content" v-model="costModelPath"/>
      </div>
      <div v-if="mode != null && this.mode.key === 'petriNet'">
        <div class="inputElmContainer">
          <span class="title limitedText" style="padding-top: 5px;">Ilm Path:&nbsp;</span>
          <input type="text" class="content" v-model="petriNetILMPath"/>
        </div>
        <div class="inputElmContainer">
          <span class="title limitedText" style="padding-top: 5px;">Res Path:&nbsp;</span>
          <input type="text" class="content" v-model="petriNetResPath"/>
        </div>
      </div>
      <div style="margin-top: 10px; border: 1px solid var(--main-font-color); padding:5px; border-radius: 8px;">
        <div class="noSelect" style="text-align: center; cursor: pointer;" @click="_onSourceConfigToggle">Source Configuration</div>
        <div v-show="showSourceConfig" class="sourceConfigContainer">
          <SimulationSourceConfig ref="sourceConfig" v-for="(s,index) in sources" v-bind:key="index" :name="s.name" :id="s.id"
                                  :sockets="s.sockets" :initialRate="s.rate" :initialData="s.data" :initialCustom="s.custom"></SimulationSourceConfig>
        </div>
      </div>
      <div style="display:inline-block; margin-top:10px;">
        <button style="display:inline; margin:4px;" @click="hide">Close</button>
        <button style="display:inline; margin:4px;" :class="canExecute ? '' : 'disabled'" @click="_confirm">Simulate</button>
      </div>
    </div>
  </modal>
</template>

<script>

import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import SimulationSourceConfig from "@/components/features/simulator/SimulationSourceConfig.vue";
import {safeVal} from "@/scripts/tools/Utils";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";
import {PipelineService, PIPELINE_STATUS} from "@/scripts/services/pipelineState/PipelineService";
import {NetworkService} from "@/scripts/services/network/NetworkService";
import {system} from "@/main";

export default {
  name: 'PipelineSimulationModal',
  components: {SimulationSourceConfig},

  data() {
    return {
      modeOptions: [{'title': 'Interactive', 'key': 'interactive'},
        {'title': 'PetriNet', 'key': 'petriNet'}],
      mode: null,
      duration: 30,
      costModelPath: "",
      petriNetILMPath: "",
      petriNetResPath: "",
      sources: [],
      showSourceConfig: false,
      lastSourceConfigData: ""
    }
  },

  computed: {
    canExecute() {
      if(this.mode == null) return false;

      if(this.costModelPath == null || this.costModelPath.trim().length === 0) return false;

      if(this.mode.key === "petriNet") {
        if(this.petriNetILMPath == null || this.petriNetILMPath.trim().length === 0) return false;
        if(this.petriNetResPath == null || this.petriNetResPath.trim().length === 0) return false;
      }

      return true;
    }
  },

  methods: {
    show () {
      this.sources = [];

      for(let op of PipelineService.getAllOperators()) {
        if(op.component.source) {

          let rate = 15;
          let data = null;
          let custom = "";
          let sockets = op.outputs.size;

          if(this.lastSourceConfigData != null) {
            for(let cfg of this.lastSourceConfigData) {
              if(cfg.id === op.id) {
                rate = cfg.rate;
                data = cfg.data;
                custom = cfg.custom;

                break;
              }
            }
          }

          this.sources.push({"name": op.viewName, "id": op.id, "rate": rate, "data": data, "custom": custom, "sockets": sockets});
        }
      }
      this.$modal.show('PipelineSimulationModal');
    },

    hide () {
      this.lastSourceConfigData = this._getSourceConfigs();
      this.$modal.hide('PipelineSimulationModal');
    },

    _onChange(e) {
      this.mode = e;
    },

    _onSourceConfigToggle() {
      this.showSourceConfig = !this.showSourceConfig;
    },

    _confirm() {
      if(!this.canExecute) return;

      // Construct meta data

      let opRealNameLookup = {};
      for(let op of PipelineService.getAllOperators()) opRealNameLookup["" + op.id] = op.viewName;

      let meta = {"realOpNames": opRealNameLookup, "costModelPath": this.costModelPath};

      if(this.mode.key === "petriNet") {
        meta["ilmPath"] = this.petriNetILMPath;
        meta["resPath"] = this.petriNetResPath;
      }

      this._startSimulation({"mode": this.mode.key, "duration": parseFloat(this.duration),
        "sources": this._getSourceConfigs(), "metaData": meta});

      this.hide();
    },

    _startSimulation(simulateData) {
      if(!PipelineService.isPipelineStopped()) return;

      for (let v of PipelineService.getAllOperators()) v.component.reset(v);

      PipelineService.setPipelineStatus(PIPELINE_STATUS.STARTING);

      NetworkService.simulate(PipelineService.createPipelineData(), simulateData, system.getStartMetaData()).then((res) => {
        if((res === null || !res["res"]) && PipelineService.isPipelineStarting()) PipelineService.setPipelineStatus(PIPELINE_STATUS.STOPPED);
        //TODO: Could show error (res["error"]) here
      });
    },

    _getSourceConfigs() {
      let sourceConfigs = [];

      if(this.$refs.sourceConfig != null) {
        for(let cfg of this.$refs.sourceConfig) {
          sourceConfigs.push(cfg.getData());
        }
      }

      return sourceConfigs;
    },

    reset() {
      this.mode = this.modeOptions[0];
      this.duration = 0;
    },

    // EXPORT INTERFACE

    _getSaveData() {
      return {"mode": this.mode.key, "duration": this.duration, "sources": this.lastSourceConfigData,
        "costModelPath": this.costModelPath,
        "petriNetILMPath": this.petriNetILMPath, "petriNetResPath": this.petriNetResPath}
    },

    _loadSaveData(saveData) {
      this.duration = saveData.duration;
      this.mode = this.modeOptions.find(el => el.key === saveData.mode);
      this.costModelPath = safeVal(saveData.costModelPath);
      this.petriNetILMPath = safeVal(saveData.petriNetILMPath);
      this.petriNetResPath = safeVal(saveData.petriNetResPath);

      this.lastSourceConfigData = saveData.sources;
    }
  },

  mounted() {
    this.reset();

    DataExportService.registerDataExporter("simulator", this._getSaveData, this._loadSaveData);

    registerEvent(EVENTS.CLEAR_PIPELINE, this.reset);
  }
}
</script>

<style scoped>
.title {
  width: 100px;
  text-align: left;
}

.content {
  width: calc(100% - 75px);
  box-sizing: border-box;
  font-size: inherit;
  color: inherit;
}

.sourceConfigContainer {
  max-height: 400px;
  overflow-y: auto;
  padding-bottom: 5px;
}

.inputElmContainer {
  display:flex;
  flex-direction: row;
  margin-top: 10px;
  height: 34px;
}
</style>
