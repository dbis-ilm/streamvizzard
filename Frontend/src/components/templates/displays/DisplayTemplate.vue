<template>
  <div style="height:100%; width:100%;">
    <div ref="container" :title="tooltip"></div>
  </div>
</template>

<script>
import Vue from "vue";
import "vue-select/dist/vue-select.css";
import {getDataTypeForName} from "@/scripts/components/modules";
import {makeResizable} from "@/scripts/tools/Utils";
import $ from "jquery";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";

export default {
  props: ['getData', 'putData', 'tooltip', 'node', 'ctrl', 'initialDataType'],
  data() {
    return {
      value: null,

      currentTemplate: null,
      currentDisplayElement: null,
      currentDisplayVariant: null,

      displayMode: 0,
      dataType: null,
      displaySocket: 0,

      dataStructure: null, //The structure of the data
      dataInspect: null, //The inspect command from UI

      settings: null
    }
  },
  methods: {
    removeDisplay() {
      if(this.currentDisplayElement == null) return;

      this.node.vueContext.unregisterResizable("DT");

      this.currentDisplayElement.$el.remove();
      this.currentDisplayElement.$destroy();
      this.currentDisplayElement = null;
      this.currentDisplayVariant = null;

      this.settings = null; //If in reset it will produce weird result on pipeline start and remove size of element

      this._updateConnections();
    },

    onValueUpdated(val) {
      this.value = val;

      if(this.value == null) this.reset();
      else if(this.currentDisplayElement != null) this.currentDisplayElement.setValue(this.value);
    },

    reset(resetInspect = false) {
      if(this.currentDisplayElement != null) {
        this.currentDisplayElement.setValue(null);

        if(this.currentDisplayElement.reset !== undefined)
          this.currentDisplayElement.reset();
      }

      if(resetInspect) {
        this.dataStructure = null;
        this.dataInspect = null;

        this.node.component.editor.trigger("onNodeDataInspectChanged", this);
      }

      this.value = null;
    },

    onSettingsChanged(settings) {
      this.settings = settings;
      this.ctrl.onDisplayChanged(this.node);
    },

    setSettings(settings, trigger=true) {
      if(this.currentDisplayElement != null) {
        if(this.currentDisplayElement.setSettings !== undefined) this.currentDisplayElement.setSettings(settings);
        if(trigger) this.onSettingsChanged(settings);
      }
    },

    handleDisplayModeUpdate(newDT, trigger=true) {
      // GET TEMPLATE FOR DATATYPE

      const dt = getDataTypeForName(newDT);

      if(newDT == null || dt == null) {
        if(this.dataType == null) return; //Already cleared

        //Clear

        this.dataType = null;
        this.displayModeOptions = [];
        this._updateTemplate(null, trigger);

        return;
      }

      if(this.dataType !== dt) {
        this.reset();

        this.displayMode = 0; //Switch to first option
        if(trigger) this.ctrl.onDisplayChanged(this.node); //Inform server

        this.dataType = dt;

        //Update template to new data type  based on display type
        const dm = dt.getDisplayMode(this.displayMode);
        if(dm == null) return null;

        this._updateTemplate(dm, Object.assign({}, dm.props), trigger); //Clone props

        this.node.component.editor.trigger("onNodeDMChanged", this);
      } else {
        //Same data type, check if also same template
        const dm = dt.getDisplayMode(this.displayMode);
        if(dm == null || this.currentTemplate === dm.template) {
          //Same template, but different variant, update settings
          if(this.currentDisplayVariant !== dm) this.setSettings(Object.assign({}, dm.props));
          this.currentDisplayVariant = dm;

          return null;
        }

        this._updateTemplate(dm, Object.assign({}, dm.props), trigger);
      }
    },

    switchDisplayMode(displayModeID) {
      let prev = this.node.component.getMonitorData(this.node);

      this.displayMode = displayModeID;

      this.ctrl.onDisplayChanged(this.node);

      this.handleDisplayModeUpdate(this.dataType.name);

      this.node.component.editor.trigger("onNodeDMChanged", this);
      executeEvent(EVENTS.NODE_DISPLAY_CHANGED, [this.node, prev]);
    },

    switchDisplaySocket(displaySocketID) {
      let prev = this.node.component.getMonitorData(this.node);

      this.displaySocket = displaySocketID;

      this.ctrl.onDisplayChanged(this.node);

      this.reset();

      this.node.component.editor.trigger("onNodeDSChanged", this);
      executeEvent(EVENTS.NODE_DISPLAY_CHANGED, [this.node, prev]);
    },

    switchDataInspect(inspect) {
      let prev = this.node.component.getMonitorData(this.node);
      this.dataInspect = inspect;

      this.ctrl.onDisplayChanged(this.node);
      executeEvent(EVENTS.NODE_DISPLAY_CHANGED, [this.node, prev]);
    },

    handleDataStructure(structure) {
      if(structure !== undefined) {
        //Only override structure if it was changed, otherwise use cached
        if(Object.keys(structure).length !== 0) {
          this.dataStructure = structure;

          this.node.component.editor.trigger("onNodeDataInspectChanged", this);
        }
      } else {
        this.dataStructure = null;

        this.node.component.editor.trigger("onNodeDataInspectChanged", this);
      }
    },

    getDefaultSettings() {
      return this.displayMode != null ? Object.assign({}, this.displayMode.props) : null;
    },

    getSettingsOptions() {
      if(this.currentDisplayElement != null) return this.currentDisplayElement.getSettingsOptions(this.settings, this.currentDisplayVariant.props);
      return [];
    },

    _updateTemplate(dm, settings, trigger) {
      // HANDLE OLD DISPLAY

      if(this.currentDisplayElement != null) {
        this.reset();

        if(dm != null && this.currentTemplate === dm.template) {
          //Same display, update props
          this.setSettings(settings, trigger);

          return;
        }

        this.removeDisplay();
      }

      if(dm == null) {
        if(trigger) this.node.component.editor.trigger("onNodeDTChanged", this);

        return;
      }

      // CREATE NEW DISPLAY

      const componentClass = Vue.extend(dm.template);
      const instance = new componentClass({
        propsData: {value: this.value, tooltip: this.tooltip, control: this}
      });

      instance.$mount();

      this.$refs.container.appendChild(instance.$el);

      this.currentDisplayElement = instance;
      this.currentTemplate = dm.template;
      this.currentDisplayVariant = dm;

      makeResizable($(instance.$el), this.node, "DT");

      this.setSettings(settings, trigger);

      this._updateConnections();

      if(trigger) this.node.component.editor.trigger("onNodeDTChanged", this);
    },

    _updateConnections() {
      this.node.component.editor.view.updateConnections({ node: this.node });
      setTimeout(() => {
        this.node.component.editor.view.updateConnections({ node: this.node });
      }, 10);
    }
  },

  mounted() {
    this.handleDisplayModeUpdate(this.initialDataType, false);
  },

  beforeDestroy() {
    this.removeDisplay();
  }
}
</script>

<style scoped>

</style>
