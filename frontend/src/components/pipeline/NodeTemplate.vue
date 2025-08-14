<template>
  <div ref="node" class="node" :class="[selected(), node.name, 'mod_' + node.component.path[0]] | kebab" :style="'background:' + node.component.bgColor">
    <div class="ctrlRow">
      <div class="titleContainer" :title="node.viewName"><AutoScaleTextarea ref="nameInput" :value="node.viewName" class="title editorInput" @change=onViewNameChange($event)></AutoScaleTextarea></div>
      <div style="right: -10px; top: -7px; position:absolute;">
        <i :class="'ctrlIcon bi bi-sliders2-vertical ' + (node.settingsEnabled ? '' : 'activated')" title="Show / Hide operator settings" @click="onSettingsToggleClick()"></i>
        <i :class="'ctrlIcon bi bi-graph-up ' + (node.dataMonitorEnabled ? '' : 'activated')" title="Show / Hide data monitor" @click="onMonitorToggleClick()"></i>
        <i class="ctrlIcon bi bi-x-circle" title="Remove Operator" @click="onRemove()" @pointerdown.stop=""></i>
      </div>
      <div style="left: -10px; top: -7px; position:absolute;">
        <i class="bi bi-stop-circle ctrlIcon" v-if="system != null && system.debuggerEnabled && hasActiveBreakpoint" :style="'visibility:visible; ' + (hasTriggeredBreakpoint ? 'color:red;' : '')"
           :title="hasTriggeredBreakpoint ? 'Breakpoint triggered!' : 'Has active breakpoints!'"></i>
        <i class="bi bi-question-circle ctrlIcon" v-if="advisorSuggestions != null" style="visibility:visible; color: red;" title="Advisions are available!"></i>
        <i class="bi bi-exclamation-circle ctrlIcon" v-if="errorMsg != null" style="visibility:visible; color: red;" title="An error occurred!"></i>
        <i class="bi bi-info-circle ctrlIcon" v-if="manualCompileTarget" style="visibility:visible;" title="Operator has manual compilation target!"></i>
        <i class="bi bi-shuffle ctrlIcon" v-if="outOfOrderOccurrence" style="visibility:visible;" title="Operator processes out-of-order tuples!"></i>
      </div>
    </div>
    <div class="content">
      <div class="col">
        <div class="input" v-for="input in inputs()" :key="input.key" style="text-align: left">
          <Socket ref="inSocks" v-socket:input="input" type="input" :name="input.name" :socket="input.socket" :sKey="input.key" :used="() => input.connections.length"></Socket>
          <input type="text" v-show="!input.showControl()" :value="input.name" @change="onSocketNameChange(input, $event)" v-on:keyup.enter="onNameSubmit($event)" class="socketInput input-title editorInput" style="text-align:left;">
          <div class="input-control" v-show="input.showControl()" v-control="input.control"></div>
        </div>
      </div>
      <div class="col mainContent" ref="mainContent" :id="'content' + node.id" v-if="node.controls.size&gt;0 || node.inputs.size&gt;0">
        <div :class="'control ' + (control.dataMonitor ? 'dataMonitor' : '')" v-for="control in controls()" v-control="control" :key="control.key"
             v-show="(control.dataMonitor && node.dataMonitorEnabled) || (!control.dataMonitor && node.settingsEnabled)"></div>
      </div>
      <div class="col">
        <div class="output" v-for="output in outputs()" :key="output.key">
          <input type="text" :value="output.name" @change="onSocketNameChange(output, $event)" v-on:keyup.enter="onNameSubmit($event)" class="socketInput output-title editorInput" style="text-align:right;">
          <Socket ref="outSocks" v-socket:output="output" type="output" :socket="output.socket" :name="output.name" :sKey="output.key"></Socket>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import mixin from 'rete-vue-render-plugin/src/mixin';
import Socket from './SocketTemplate.vue';
import {system} from "@/main";

import $ from 'jquery'
import {applyResize, makeNameInput, registerAutoBorderSize} from "@/scripts/tools/Utils";
import {EVENTS, executeEvent, registerEvent} from "@/scripts/tools/EventHandler";
import AutoScaleTextarea from "@/components/interface/elements/base/AutoHeightTextarea.vue";

export default {
  mixins: [mixin],
  components: {
    AutoScaleTextarea,
    Socket
  },
  data() {
    return {
      system: null,

      heatmapRating: 0.0,

      advisorSuggestions: null,

      errorMsg: null,

      hasActiveBreakpoint: false,
      hasTriggeredBreakpoint: false,
      breakPoints: [],

      resizeElements: new Map()
    }
  },
  methods: {
    onSettingsToggleClick: function() {
      this.node.component.setOperatorSettingsState(this.node, !this.node.settingsEnabled);
    },

    onMonitorToggleClick: function() {
      this.node.component.setDataMonitorState(this.node, !this.node.dataMonitorEnabled);
    },

    onRemove: function() {
      this.node.component.editor.removeNode(this.node);
    },

    updateMessageBroker: function(broker) {
      let socks = this.$refs.inSocks;

      if(broker == null) {
        if(socks != null) {
          for(let i=0; i < socks.length; i++) socks[i].reset();
        }

        return;
      }

      if (socks == null) return;

      for(let i = 0; i < Math.min(broker.msg.length, socks.length); i++) {
        socks[i].updateMessageCount(broker.msg[i], broker.max);
      }
    },

    onViewNameChange: function(event) {
      let prevValue = this.node.viewName;

      this.node.viewName = event.target.value;
      if(this.node.viewName === "") this.node.viewName = this.node.component.displayName;

      executeEvent(EVENTS.NODE_NAME_CHANGED, [this.node, prevValue]);
    },

    onNameSubmit: function(event) {
      $(event.target).blur();
    },

    onSocketNameChange: function(socket, event) {
      let prevValue = socket.name;

      socket.name = event.target.value;

      if(socket.name === "") socket.name = socket.defaultName;

      this.node.update();

      executeEvent(EVENTS.NODE_SOCKET_NAME_CHANGED, [this.node, socket, prevValue]);
    },

    getSocketVueContext(inSocket, key) {
      let socks = inSocket ? this.$refs.inSocks : this.$refs.outSocks;

      for(let s of socks) {
        if(s["sKey"] === key) return s;
      }

      return null;
    },

    updateError(error) {
      this.errorMsg = error;
    },

    updateAdvisorSuggestion(suggestions) {
      //Suggestions may be null if there are no longer suggestions
      this.advisorSuggestions = suggestions;

      this.node.component.editor.trigger("onNodeAdvisorChanged", this.node);
    },

    updateBreakpoints(bps) {
      this.breakPoints = bps;
      this.hasTriggeredBreakpoint = false;

      this.hasActiveBreakpoint = false;

      for(let p of bps) {
        if (p.enabled) {
          this.hasActiveBreakpoint = true;
          break;
        }
      }

      this.node.component.sendMetaDataUpdate(this.node);
    },

    setBreakpointTriggered(index) {
      if(this.breakPoints.length > index)
        this.hasTriggeredBreakpoint = true;
    },

    reset() {
      this.hasTriggeredBreakpoint = false;
      this.updateAdvisorSuggestion(null);
      this.updateError(null);
      this.updateMessageBroker(null);
    },

    //--------------- Track and Apply Resizes ---------------

    resizeElement(key, width, height) {
      if(!this.resizeElements.has(key)) return;

      applyResize(this.resizeElements.get(key), {"width": width, "height": height});
    },

    onElementResize(key, size) {
      if(!this.resizeElements.has(key)) return;

      let prevData = this.getResizeData();

      //All elements need to have the same width

      for(let [,v] of this.resizeElements) v.width(size.width);

      this.node.component.editor.trigger("nodeResized", {"node": this.node, "prev": prevData});
    },

    getResizeData() {
      let cr = [];

      for(let [k, v] of this.resizeElements) cr.push({"id": k, "data": {"width": v.width(), "height": v.height()}});

      return cr;
    },

    registerResizable(element, key) {
      this.resizeElements.set(key, element);
    },

    unregisterResizable(key) {
      this.resizeElements.delete(key);
    }
  },

  computed: {
    manualCompileTarget() {
      return this.node.compileData != null &&
          this.node.compileData["config"] != null &&
          this.node.compileData["config"]["manual"];
    },

    outOfOrderOccurrence() {
      return this.node.compileData?.["meta"]?.["outOfOrderProcessing"] || this.node.compileData?.["meta"]?.["outOfOrderJoin"];
    },
  },

  mounted() {
    this.system = system;

    makeNameInput($(this.$refs.nameInput.$el), $(this.$refs.nameInput.$el).closest("div"));

    registerAutoBorderSize(this.$el, 2, (zoomFac) => {
      let blurSize = Math.max(4, (zoomFac * 4));
      this.$el.style.boxShadow = "0 0 0 " + blurSize + "px var(--main-font-color)";
    });

    $(this.$refs.node).find('.socketInput').each(function() {
      makeNameInput($(this), $(this).closest("div"));
    });

    registerEvent(EVENTS.HISTORY_STATE_CHANGED, (enabled) => {if(!enabled) this.hasTriggeredBreakpoint = false;});
  }
}

</script>

<style>

.node:not(.selected) {
  box-shadow:none !important;
}

.node.selected {
  border-color: transparent !important;
}

div:has(> .node.selected) {
  z-index:1;
}

.ctrlIcon.activated {
  opacity: 0.25;
}

</style>

<style scoped>
.node {
  border: var(--node-border);
  border-radius: var(--node-border-radius);
  cursor: pointer;
  min-width: 180px;
  min-height: 180px;
  /*max-width: 220px;*/
  height: auto;
  padding-bottom: 6px;
  box-sizing: content-box;
  position: relative;
  user-select: none;
}
.node .output {
  text-align: right; }
.node .input {
  text-align: left; }
.node .content {
  width: 100%;
  height: calc(100% - 56px); /* 40 + padding */
  padding-bottom: 10px;
  display:flex;
  flex-direction: column;
}

.node .mainContent {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  margin-left: 10px;
  margin-right: 10px;
  width: calc(100% - 20px);
  height: 100%;
}
.node .input-title, .node .output-title {
  vertical-align: middle;
  color: white;
  display: inline-block;
  font-size: 16px;
  line-height: 24px;
}

.node .input-control {
  z-index: 1;
  width: calc(100% - 36px);
  vertical-align: middle;
  display: inline-block; }

.node .control:not(.dataMonitor) {
  margin: 4px 0;
}

.node .heatmap {
  position: absolute;

  width: 100%;
  height: 100%;

  z-index: -50;
}

.node .title {
  width: 100%;
  color: white;
  font-size: 26px;
  padding: 0;
  cursor: pointer;
  text-align:center;
  border:none;
  background-image:none;
  background-color:transparent;
  -webkit-box-shadow: none;
  -moz-box-shadow: none;
  box-shadow: none;

  resize: none;
}

.node .titleContainer {
  padding-top: 20px;
}

.node .ctrlRow {
  height: unset;
  top: unset;

  margin: 5px 10px 10px;
}

.node .title:focus, .node .socketInput:focus {
  outline: none;
}

.socketInput {
  padding-top:0 !important;
  padding-bottom:0 !important;
  cursor: pointer;
  border:none;
  background-image:none;
  background-color:transparent;
  -webkit-box-shadow: none;
  -moz-box-shadow: none;
  box-shadow: none;
}

</style>
