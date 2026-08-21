<template>
  <div>
    <CollapseHeader :openedDir="'up'" class="sectionHeader" v-model="$streamvizzard.monitor.showSidebar" title="Monitor">
      <i :class="['bi bi-file-code' + ($streamvizzard.monitor.showSidebarTransformer ? '-fill' : ''), 'clickableIcon toggleIcon toggleTransformerIcon', !operator.showData && 'disabled']"
         title="Toggle the display data transformer to visualize the produced operator output data in a custom way." @click="_toggleDataTransformer($event)"></i>
      <i :class="'bi bi-bar-chart-line' + ($streamvizzard.monitor.showSidebarStats ? '-fill' : '') + ' clickableIcon toggleIcon toggleStatsIcon'"
         title="Toggle the operator execution statistics" @click="_toggleExecutionStats($event)"></i>
      <i class="bi bi-hourglass-split warningIcon toggleIcon" v-if="operator.monitor.executionStats.perfWarning" title="Operator has a performance warning!"></i>
    </CollapseHeader>

    <div class="monitorContent" v-show="$streamvizzard.monitor.showSidebar">

      <div class="limitedText warningContent" v-if="operator.monitor.executionStats.perfWarning">{{operator.monitor.executionStats.perfWarning}}</div>

      <div v-if="operator.showData">
        <div class="limitedText" v-if="socketOutCount > 0">Display Type: {{ dataType }}</div>

        <div v-if="socketOutCount > 1" class="formInputContainer">
                <span class="formInputLabel"
                      title="The produced data of which output socket should be used to visualize">Display Socket:&nbsp;</span>
          <v-select v-auto-blur ref="displaySocket" :clearable="false" :searchable="false" :options="displaySocketOptions"
                    class="formInputField" :value="displaySocketSelected"
                    @input="_onDisplaySocketSwitched($event)" @dblclick.stop="" @pointermove.stop=""
                    label="title"></v-select>
        </div>

        <div v-if="socketOutCount === 0">Operator is a data sink!</div>

        <div v-if="displayModeOptions.length > 0" class="formInputContainer">
          <span class="formInputLabel" title="How the data produced by this operator should be visualized">Display Mode:&nbsp;</span>
          <v-select v-auto-blur ref="displayMode" :clearable="false" :searchable="false"
                    :options="displayModeOptions" class="formInputField" :value="displayModeSelected"
                    @input="_onDisplayModeSwitched($event)" @dblclick.stop="" @pointermove.stop=""
                    label="title"></v-select>
          <i :class="'bi ' + (displayModeSettingsOpen ? 'bi-gear-fill' : 'bi-gear') + ' settingsToggle'" title="Display Mode Settings"
             @click="_onDisplayModeSettingsClicked"></i>
        </div>

        <div v-if="displayModeSettingsOpen" class="vOffset">
          <hr>
          <div ref="dmSettingContainer">
            <div v-if="displayModeSettingsEl.length === 0">No settings available!</div>
          </div>
          <hr>
        </div>
      </div>

      <div v-if="!operator.showData">Data Display disabled!</div>

      <DataTransformer :operator="operator" v-if="operator.showData && $streamvizzard.monitor.showSidebarTransformer" class="vOffset"/>

      <ExecutionStats :operator="operator" v-if="$streamvizzard.monitor.showSidebarStats" class="vOffset"/>

      <div v-if="dataStructure != null && operator.showData" class="vOffset">
        <div class="inspectTitle">Data Inspect</div>
        <StructureInspectElement :data="dataStructure" :entryKey="dataStructure['name']" :parentKey="null" :operator="operator"/>
      </div>
    </div>
  </div>
</template>

<script>

import CollapseHeader from "@/components/interface/elements/base/CollapseHeader.vue";
import Vue from "vue";
import ExecutionStats from "@/components/features/monitor/sidebar/ExecutionStats.vue";
import {formatTime, valueOr} from "@/scripts/tools/Utils";
import {EVENTS, registerEvent, unregisterEvent} from "@/scripts/tools/EventHandler";
import DataTransformer from "@/components/features/monitor/sidebar/DataTransformer.vue";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";
import StructureInspectElement from "@/components/features/monitor/sidebar/StructureInspectElement.vue";

export default {
  components: {StructureInspectElement, DataTransformer, ExecutionStats, CollapseHeader},
  props: {
    operator: {type: SvOperator, required: true},
  },

  data() {
    return {
      socketOutCount: 0,

      displayModeOptions: [],
      displayModeSelected: null,

      displayModeSettingsOpen: false,
      displayModeSettingsEl: [],

      displaySocketOptions: [],
      displaySocketSelected: null,
    }
  },

  watch: {
    operator() { // First listen to operator change, other listener might get called too
      this._onOpInitialized();
    },

    displaySocket() {
      this._onSocketsChanged();
    },

    socketOutCount() {
      this._onSocketsChanged();
    },

    displayMode() {
      this._updateDisplayData();
    },

    dataType() {
      this._updateDisplayData();
    }
  },

  computed: {
    displaySocket() {
      return this.operator.monitor.displaySocket;
    },

    displayMode() {
      return this.operator.monitor.displayMode;
    },

    dataType() {
      let dt = this.operator.monitor.displayDataType;

      if(dt !== null) return dt.displayName;
      else return "Unknown (" + this.operator.monitor.rawDataType + ")";
    },

    dataStructure() {
      return this.operator.monitor.displayDataStructure;
    }
  },

  methods: {
    formatTime,
    _onOpInitialized() {
      this._updateOutSocketCount(this.operator);

      this._toggleDisplayModeSettings(false);
      this._updateDisplayData();
      this._onSocketsChanged();
    },

    _updateDisplayData() {
      let dt = this.operator.monitor.displayDataType;

      if(dt !== null) {
        let dm = this.displayMode;

        // CREATE OPTIONS MENU

        this.displayModeOptions = [];

        for(let [k, v] of dt.getAllDisplayModes().entries()) {
          this.displayModeOptions.push({'title': v.name, 'key': k});
        }

        this.displayModeSelected = this.displayModeOptions.find(el => el.key === dm.modeID);

        // Update settings if open
        if(this.displayModeSettingsOpen) this._toggleDisplayModeSettings(true);
      } else {
        this.displayModeOptions = [];
        this.displayModeSelected = null;

        this._toggleDisplayModeSettings(false);
      }
    },

    _onDisplayModeSwitched(event) {
      let newDm = this.operator.monitor.displayDataType.getDisplayMode(event.key, true);
      this.operator.monitor.updateDisplayMode(newDm);

      this.displayModeSelected = this.displayModeOptions.find(el => el.key === this.operator.monitor.displayMode.modeID);

      this.$refs.displayMode.$el.blur();
    },

    // DisplayMode settings

    _onDisplayModeSettingsClicked() {
      this._toggleDisplayModeSettings(!this.displayModeSettingsOpen);
    },

    _toggleDisplayModeSettings(open) {
      this.displayModeSettingsOpen = open;

      if(open) {
        // Add elements delayed to give time for v-if enabling

        let self = this;
        let monitor = this.operator.monitor;

        Vue.nextTick(function () {
          self._clearDisplayModeSettings();

          let container = self.$refs.dmSettingContainer;
          let settings = monitor.displayMode.getSettingsOptions(monitor.displayModeSettings);

          for (let setting of settings) {
            const componentClass = Vue.extend(setting.template);
            const instance = new componentClass({
              propsData: {
                skey: setting.key, name: setting.name, desc: setting.desc, data: setting.data,
                default: setting.def, value: setting.value, change: (key, val) => {
                  let set = valueOr(Object.assign({}, monitor.displayModeSettings), {}); // Cloned to not modify the orig obj
                  set[key] = val;
                  monitor.updateDisplayModeSettings(set);
                }
              }
            });

            self.displayModeSettingsEl.push(instance);

            instance.$mount();

            container.appendChild(instance.$el);
          }
        });
      } else this._clearDisplayModeSettings();
    },

    _clearDisplayModeSettings() {
      for(let i = 0; i < this.displayModeSettingsEl.length; i++) {
        let elem = this.displayModeSettingsEl[i];

        elem.$el.remove();
        elem.$destroy();
      }

      this.displayModeSettingsEl = [];
    },

    // Sockets

    _updateOutSocketCount(operator) {
      if(operator === this.operator) this.socketOutCount = this.operator.outputs.length;
    },

    _onDisplaySocketSwitched(event) {
      this.displaySocketSelected = event;

      this.operator.monitor.updateDisplaySocket(event.key);

      if(this.$refs.displayMode != null) this.$refs.displayMode.$el.blur();
    },

    _onSocketsChanged() {
      let options = [];

      for (const o of this.operator.outputs) {
        options.push({'title': o.name, 'key': o.id});
      }

      this.displaySocketOptions = options;

      if(options.length > 0)
        this.displaySocketSelected = this.displaySocketOptions.find(el => el.key === this.operator.monitor.displaySocket);
      else this.displaySocketSelected = null;
    },

    // Stats plot

    _toggleExecutionStats(event) {
      this.$streamvizzard.monitor.showSidebarStats = !this.$streamvizzard.monitor.showSidebarStats;

      event.stopPropagation();
    },

    // Transformer

    _toggleDataTransformer(event) {
      this.$streamvizzard.monitor.showSidebarTransformer = !this.$streamvizzard.monitor.showSidebarTransformer;

      event.stopPropagation();
    },
  },

  mounted() {
    this._onOpInitialized();

    registerEvent(EVENTS.OP_SOCKET_COUNT_CHANGED, this._updateOutSocketCount);
  },

  beforeDestroy() {
    unregisterEvent(EVENTS.OP_SOCKET_COUNT_CHANGED, this._updateOutSocketCount);
  }
}

</script>

<style scoped>

.monitorContent {
  padding-top: 10px;
}

.formInputLabel {
  width: 117px;
  text-align: left;
}

.settingsToggle {
  width: 30px;
  font-size: 24px;
  padding-top: 1px;
  margin-left: 4px;
  cursor: pointer;
}

.inspectContainer {
  max-height: 400px;
  overflow-y: auto;
  margin-top: 10px;
}

.inspectTitle {
  text-decoration: underline;
}

.toggleIcon {
  position: absolute;
  padding: 4px;
  margin-top: -4px;
}

.toggleStatsIcon {
  margin-left: 24px;
  transform: scaleX(1.2);
}

.toggleTransformerIcon {
  margin-left: 3px;
}

.warningIcon {
  color: var(--warning-color);
  left: 0;
}

.warningContent {
  margin-bottom: 5px;
  white-space: break-spaces;
  font-style: italic;
  max-height: 4.2em;
  overflow-y: auto;
  overflow-x: hidden;
  color: var(--warning-color);
}

</style>
