<template>
  <modal ref="modal" name="PipelineSimulationModal" transition="pop-out" :width="300" height="auto" :shiftY="0" :shiftX="0.075" style="top: 10%;">
    <div style="padding:10px;">
      <div style="text-decoration: underline;"><b>Simulate Pipeline</b></div>
      <br/>
      <div style="display:flex; flex-direction: row; height: 34px;">
        <div class="title" style="padding-top: 5px;">Duration:&nbsp;</div>
        <input class="content" title="How many seconds the simulation should calculate" type="number" v-model="duration">
      </div>
      <div style="display:flex; flex-direction: row; margin-top: 10px;">
        <span class="title" style="padding-top: 5px;">Mode:&nbsp;</span>
        <v-select class="content" :options="modeOptions" label="title" :value="mode" :clearable="false" :searchable="false" @input="_onChange($event)"></v-select>
      </div>
      <div style="margin-top: 10px; border: 1px solid #444444; padding:5px; border-radius: 8px;">
        <div class="noSelect" style="text-align: center; cursor: pointer;" @click="_onSourceConfigToggle">Source Configuration</div>
        <div v-show="showSourceConfig" class="sourceConfigContainer">
          <SimulationSourceConfig ref="sourceConfig" v-for="(s,index) in sources" v-bind:key="index" :name="s.name" :id="s.id"
                                  :sockets="s.sockets" :initialRate="s.rate" :initialData="s.data" :initialCustom="s.custom"></SimulationSourceConfig>
        </div>
      </div>
      <div style="display:inline-block; margin-top:10px;">
        <button style="display:inline; margin:4px;" @click="hide">Close</button>
        <button style="display:inline; margin:4px;" @click="_confirm">Simulate</button>
      </div>
    </div>
  </modal>
</template>

<script>

import {operatorLookup, registerDataExporter, sendPipelineSimulate} from "@/components/Main";
import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import SimulationSourceConfig from "@/components/templates/tools/simulation/SimulationSourceConfig";

export default {
  name: 'PipelineSimulationModal',
  components: {SimulationSourceConfig},

  data() {
    return {
      modeOptions: [{'title': 'Interactive', 'key': 'interactive'},
        {'title': 'PetriNet', 'key': 'petriNet'}],
      mode: null,
      duration: 30,
      sources: [],
      showSourceConfig: false,
      lastSourceConfigData: ""
    }
  },

  methods: {
    show () {
      this.sources = [];

      for(let op of operatorLookup.values()) {
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
      sendPipelineSimulate({"mode": this.mode.key, "duration": parseFloat(this.duration), "sources": this._getSourceConfigs()});

      this.hide();
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
      return {"mode": this.mode.key, "duration": this.duration, "sources": this.lastSourceConfigData}
    },

    _loadSaveData(saveData) {
      this.duration = saveData.duration;
      this.mode = this.modeOptions.find(el => el.key === saveData.mode);

      this.lastSourceConfigData = saveData.sources;
    }
  },

  mounted() {
    this.reset();

    registerDataExporter("simulateData", this._getSaveData, this._loadSaveData);

    registerEvent(EVENTS.CLEAR_PIPELINE, this.reset);
  }
}
</script>

<style scoped>
.title {
  width: 75px;
  text-align: left;
}

.content {
  width: calc(100% - 75px);
  box-sizing: border-box;
}

.sourceConfigContainer {
  max-height: 400px;
  overflow-y: auto;
  padding-bottom: 5px;
}
</style>
