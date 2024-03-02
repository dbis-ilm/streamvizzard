<template>
  <div ref="node" class="node" :class="[selected(), node.name, 'mod_' + node.component.path[0]] | kebab" :style="'background:' + node.component.bgColor">
    <div class="ctrlRow" style="top: 3px; height: 64px;">
      <div class="titleContainer"><input type="text" ref="nameInput" :value="node.viewName" class="title mouseEventBlocker" @change=onViewNameChange($event)></div>
      <div style="right: 3px; top: -3px; position:absolute;">
        <i ref="collapseIcon" class="ctrlIcon bi bi-eye" title="Collapse / Expand" @click="onMonitorToggleClick()"></i>
        <i class="ctrlIcon bi bi-x-circle" title="Remove Operator" @click="onRemove()"></i>
      </div>
      <div style="left: 3px; top: -3px; position:absolute;">
        <i class="bi bi-stop-circle ctrlIcon" v-if="system != null && system.debuggerEnabled && hasActiveBreakpoint" :style="'visibility:visible; ' + (hasTriggeredBreakpoint ? 'color:red;' : '')"
           :title="hasTriggeredBreakpoint ? 'Breakpoint triggered!' : 'Has active breakpoints!'"></i>
        <i class="bi bi-question-circle ctrlIcon" v-if="advisorSuggestions != null" style="visibility:visible; color: red;" title="Advisions are available!"></i>
        <i class="bi bi-exclamation-circle ctrlIcon" v-if="errorMsg != null" style="visibility:visible; color: red;" title="An error occured!"></i>
      </div>
    </div>
    <div class="content">
      <div class="col">
        <div class="input" v-for="input in inputs()" :key="input.key" style="text-align: left">
          <Socket ref="inSocks" v-socket:input="input" type="input" :name="input.name" :socket="input.socket" :used="() => input.connections.length"></Socket>
          <input type="text" v-show="!input.showControl()" :value="input.name" @change="onSocketNameChange(input, $event)" v-on:keyup.enter="onNameSubmit($event)" class="socketInput input-title mouseEventBlocker" style="text-align:left;">
          <div class="input-control" v-show="input.showControl()" v-control="input.control"></div>
        </div>
      </div>
      <div class="col mainContent" ref="mainContent" :id="'content' + node.id" v-if="node.controls.size&gt;0 || node.inputs.size&gt;0">
        <div class="control" v-for="control in controls()" v-control="control" :key="control.key"></div>
      </div>
      <div class="col">
        <div class="output" v-for="output in outputs()" :key="output.key">
          <input type="text" :value="output.name" @change="onSocketNameChange(output, $event)" v-on:keyup.enter="onNameSubmit($event)" class="socketInput output-title mouseEventBlocker" style="text-align:right;">
          <Socket v-socket:output="output" type="output" :socket="output.socket" :name="output.name"></Socket>
        </div>
      </div>
    </div>
    <div class="stats">
      <Stats ref="stats" v-if="showStats"></Stats>
    </div>
  </div>
</template>

<script>
import mixin from 'rete-vue-render-plugin/src/mixin';
import Socket from './SocketTemplate';
import Stats from './StatsTemplate';
import {system} from "@/main";

import $ from 'jquery'
import {applyResize, makeNameInput, registerAutoBorderSize} from "@/scripts/tools/Utils";
import {EVENTS, executeEvent, registerEvent} from "@/scripts/tools/EventHandler";

export default {
  mixins: [mixin],
  components: {
    Socket,
    Stats
  },
  data() {
    return {
      system: null,

      monitorToggle: 'x',
      showStats: false,
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
    onMonitorToggleClick: function() {
      const data = this.node.component.getMonitorData(this.node);

      this.node.component.setDataMonitorState(this.node, !data.state.sendData);
    },

    onRemove: function() {
      this.node.component.editor.removeNode(this.node);
    },

    onStatsToggleClick: function() {
      this.node.component.toggleStatsMonitor(this.node);

      this.updateMonitorDisplay();
    },

    updateMonitorDisplay: function() {
      const data = this.node.component.getMonitorData(this.node);

      // Data

      if(!data.state.sendData) {
        $('#content' + this.node.id).find('.control').hide();
        this.$el.classList.add("collapsed");
        this.$refs.collapseIcon.classList.remove("bi-eye");
        this.$refs.collapseIcon.classList.add("bi-eye-slash");
      } else {
        $('#content' + this.node.id).find('.control').show();
        this.$el.classList.remove("collapsed");
        this.$refs.collapseIcon.classList.add("bi-eye");
        this.$refs.collapseIcon.classList.remove("bi-eye-slash");
      }

      // Stats

      this.showStats = data.state.sendStats;

      this.node.component.editor.view.updateConnections({ node: this.node });
    },

    updateStatsData: function(stats) {
      this.$refs.stats.setStats(stats);
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

  mounted() {
    this.system = system;

    this.updateMonitorDisplay();

    makeNameInput($(this.$refs.nameInput), $(this.$refs.nameInput).closest("div"));

    registerAutoBorderSize(this.$el, 2);

    $(this.$refs.node).find('.socketInput').each(function() {
      makeNameInput($(this), $(this).closest("div"));
    });

    registerEvent(EVENTS.HISTORY_STATE_CHANGED, (enabled) => {if(!enabled) this.hasTriggeredBreakpoint = false;});
  }
}

</script>

<style>

.node.selected {
  box-shadow:0 0 0 4px #555;
  border: 2px solid transparent !important;
}

</style>

<style scoped>
.node {
  border: 2px solid #828282;
  border-radius: 10px;
  cursor: pointer;
  min-width: 180px;
  min-height: 180px;
  /*max-width: 220px;*/
  height: auto;
  padding-bottom: 6px;
  box-sizing: content-box;
  position: relative;
  user-select: none; }
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
  /*overflow:hidden; -> dropdowns no more visible */
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
.node .control {
  margin: 4px 0;
}

.node .heatmap {
  position: absolute;

  width: 100%;
  height: 100%;

  z-index: -50;
}

.node .title {
  color: white;
  font-size: 26px;
  height:40px;
  width: calc(100% - 180px);
  padding: 0;
  margin-top: 10px;
  cursor: pointer;
  text-align:center;
  border:none;
  background-image:none;
  background-color:transparent;
  -webkit-box-shadow: none;
  -moz-box-shadow: none;
  box-shadow: none;

  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.node .titleContainer {
  height: 100%;

  /* Required to reduce min size of nodes -> See width: calc(100% - 80px) in title */
  margin-left: -25px;
  margin-right: -25px;
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
