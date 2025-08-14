<template>
<div id="pipelineDebugger" style="width: 30%; margin: 0 auto; display:inline-block; position: relative;">
  <EditorHistory ref="editorHistory" :canAddEvent="_onEditorHistoryEventAdded" :canUpdateEvent="_onEditorEventUpdate" :maxEvents="null" :clearRedoOnNewEvent="false"></EditorHistory>
  <div ref="rewindBwd" :class="'clickableIcon controlButton ' + (!historyActive ? 'disabled' : '')" title="Rewind Backward" @click="_rewind($event, false)" style="left: -35px;"><i class="bi bi-rewind-circle"></i></div>
  <div :class="'clickableIcon controlButton ' + (!historyActive ? 'disabled' : '')" title="1 Step Backward" @click="_stepHistory(-1)" style="left: -12px;"><i class="bi bi-arrow-left-circle"></i></div>
  <div style="display: inline-block; position: relative;">
    <div style="cursor:default;">Pipeline History <i class="bi bi-info-circle" :title="memoryString"></i></div>
    <div :class="'clickableIcon ' + (!pipelineRunning ? 'disabled' : '')" title="Toggles the history graph" @click="_toggleHistoryGraph" style="position: absolute; font-size: 26px; right: -30px; top: calc((100% - 36px)/2);"><i :class="'bi bi-diagram-2' + ($refs.historyGraph && $refs.historyGraph.isOpen ? '-fill' : '')"></i></div>
    <div v-if="system.debuggerProvenanceEnabled" :class="'clickableIcon ' + (!pipelineRunning ? 'disabled' : '')" title="Toggles the provenance inspector" @click="_toggleProvInspector" style="position: absolute; font-size: 22px; right: -56px; top: calc((100% - 29px)/2);"><i :class="'bi bi-clipboard-data' + ($refs.provInspector && $refs.provInspector.isOpen ? '-fill' : '')"></i></div>
  </div>
  <vue-slider v-model="currentStepID" :disabled="!historyActive" v-bind="options"
              :tooltip-formatter="val => _getStepString(val)" @change="_onSliderChange"
              style="display:inline-block; width: calc(100% - 40px); margin-top: -0.5px">
  </vue-slider>
  <div :class="'clickableIcon controlButton ' + (!historyActive ? 'disabled' : '')" title="1 Step Forward" @click="_stepHistory(1)" style="right: -12px;"><i class="bi bi-arrow-right-circle"></i></div>
  <div ref="rewindFwd" :class="'mirrorY clickableIcon controlButton ' + (!historyActive ? 'disabled' : '')" title="Rewind Forward" @click="_rewind($event, true)" style="right: -35px;margin-top: 0.5px;"><i class="bi bi-rewind-circle"></i></div>
  <div :class="'clickableIcon controlButton ' + (maxSteps <= 0 ? 'disabled' : '')" title="Pause / Continue the pipeline" @click="_onControlClicked" style="right: -58px;"><i :class="'bi ' + (!historyActive ? 'bi-pause-circle' : 'bi-play-circle')"></i></div>
  <HistoryGraph ref="historyGraph" @onBranchTraversal="_onBranchTraversal" :traversalAllowed="historyActive && rewind == null" @onHistoryTraversal="_toggleHistoryTraversal"></HistoryGraph>
  <ProvInspector ref="provInspector" :debugger="this" v-if="system.debuggerProvenanceEnabled" @executeQuery="_onProvQueryExecuted"></ProvInspector>
</div>
</template>

<script>
import 'vue-slider-component/theme/antd.css'
import {EVENTS, executeEvent, registerEvent} from "@/scripts/tools/EventHandler";
import {clamp, formatDataSize, formatTime} from "@/scripts/tools/Utils";
import $ from 'jquery'
import {getStepDescriptionForType} from "@/scripts/tools/debugger/DebugSteps";
import EditorHistory from "@/components/utils/editorHistory/EditorHistory.vue";
import {system} from "@/main";
import HistoryGraph from "@/components/features/debugger/HistoryGraph.vue";
import ProvInspector from "@/components/features/debugger/ProvInspector.vue";
import {PipelineUpdateService} from "@/scripts/services/pipelineUpdates/PipelineUpdateService";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";

export default {
  name: "PipelineDebugger",
  computed: {
    system() {
      return system
    },

    historyGraph() {
      return this.$refs.historyGraph;
    }
  },
  components: {ProvInspector, HistoryGraph, EditorHistory},
  data() {
    return {
      currentStepID: 1,
      currentStepTime: 0,
      maxSteps: 0,

      pipelineRunning: false,
      historyActive: false,
      historyPaused: false,  // Only set from server, true=pipelineState is paused, and we traverse manually
      rewind: null,
      memoryString: "Cache: 0MB | Disk: 0MB",

      options: {
        dotSize: 14,
        width: 'auto',
        height: 5,
        min: 0,
        max: 1,
        interval: 1,
        silent: true, //Hides error that occurs when max/value are set at the same time
        tooltipPlacement: "bottom",
        tooltip: 'hover',
        duration: 0.25,
      }
    }
  },

  methods: {
    _getStepString(val) {
      if(this.maxSteps <= 0) return 'Step: 0 / 0';

      let timeStr = (this.$refs.historyGraph.isOpen ? '| ΔTime: ' + formatTime(this.$refs.historyGraph.getCurrentDeltaTime(this.currentStepTime)) : '');

      return 'Step: ' + (val - this.options.min + 1) + ' / ' + this.maxSteps + timeStr;
    },

    _onControlClicked() {
      this._changeHistoryState(!this.historyActive);

      this.$emit('stateChange');
    },

    _onSliderChange() {
      this._removeRewind();

      this.$refs.historyGraph.signalTargetRequested(this.$refs.historyGraph.currentBranchID, this.currentStepID);

      let currentBID = this.$refs.historyGraph.currentBranchID;

      this.$emit('stepChange', currentBID, (this.currentStepID + this.$refs.historyGraph.getStepOffsetForBranch(currentBID)));
    },

    async _onBranchTraversal(branchID, stepID, targetTime, maxSteps) {
      this._removeRewind();

      this.maxSteps = maxSteps;
      this.options.max = maxSteps - 1;

      if(stepID != null) {
        this.currentStepID = stepID - this.$refs.historyGraph.getStepOffsetForBranch(branchID);
        this.$emit('stepChange', this.$refs.historyGraph.currentBranchID, stepID);
      } else {
        this.$emit('requestStep', this.$refs.historyGraph.currentBranchID, targetTime);
      }
    },

    _stepHistory(val) {
      this.currentStepID = clamp(this.currentStepID + val, this.options.min, this.options.max);

      this._onSliderChange();
    },

    _rewind(event, forward) {
      if(this.rewind == null || (this.rewind === 1 && !forward) || (this.rewind === 2 && forward)) this._setRewindStatus(forward ? 1 : 2);
      else this._setRewindStatus(null);

      this.$emit('stateChange');
    },

    _setRewindStatus(status) {
      this._removeRewind();

      this.rewind = status;

      if(this.rewind === 1) $(this.$refs.rewindFwd).addClass("activated");
      else if(this.rewind === 2) $(this.$refs.rewindBwd).addClass("activated");
    },

    _removeRewind() {
      this.rewind = null;

      $('#pipelineDebugger').find('.controlButton.activated').each(function() {
        $(this).removeClass("activated");
      });
    },

    _changeHistoryState(active) {
      if(active !== this.historyActive) executeEvent(EVENTS.HISTORY_STATE_CHANGED, active);

      this.historyActive = active;
    },

    getRewind() {
      return this.rewind;
    },

    isHistoryActive() {
      return this.historyActive;
    },

    _toggleHistoryGraph() {
      let graph = this.$refs.historyGraph;

      if(graph.isOpen) graph.close();
      else graph.open();
    },

    _toggleProvInspector() {
      let prov = this.$refs.provInspector;

      if(prov.isOpen) prov.close();
      else prov.open();
    },

    _toggleHistoryTraversal(traverse) {
      if(traverse) {
        // Stop server and history from tracking events we undo/redo manually
        PipelineUpdateService.listenForPipelineChanges(false);
        executeEvent(EVENTS.UI_HISTORY_TRAVERSE, [true, true]);
      } else {
        PipelineUpdateService.listenForPipelineChanges(true);
        executeEvent(EVENTS.UI_HISTORY_TRAVERSE, [false, true]);
      }
    },

    onReceiveRequestedStep(branchID, stepID) {
      this.$refs.historyGraph.onReceiveRequestedStep(branchID, stepID);
    },

    async updateTimeline(active, maxSteps, stepID, branchID, stepTime, branchStartTime, branchEndTime, branchStepOffset, currentMemSize, currentMemLimit, currentStorageSize, currentStorageLimit) {
      this._changeHistoryState(active);

      this.maxSteps = maxSteps;
      this.memoryString = "Cache: " + (currentMemLimit != null ? (formatDataSize(currentMemSize) + " / " + formatDataSize(currentMemLimit)) : formatDataSize(currentMemSize))
        + " | Disk: " + (currentStorageLimit != null ? (formatDataSize(currentStorageSize) + " / " + formatDataSize(currentStorageLimit)) : formatDataSize(currentStorageSize));

      this.options.max = maxSteps - 1;
      this.currentStepID = stepID - branchStepOffset;
      this.currentStepTime = stepTime;

      this.$refs.historyGraph.updateBranchData(branchID, branchStartTime, branchEndTime, maxSteps, branchStepOffset);
      await this.$refs.historyGraph.setCurrentStep(branchID, stepID, stepTime, true);

      this.historyPaused = active;
    },

    async onStepExecution(stepID, branchID, opID, type, undo, stepTime) {
      await this.$refs.historyGraph.setCurrentStep(branchID, stepID, stepTime, false);

      if(this.rewind != null) this.currentStepID = stepID; //Only set if rewinding, otherwise this leads to stuttering slider if syncing value

      this.currentStepTime = stepTime;

      if(!system.debuggerStepNotifications) return;

      let op = PipelineService.getOperatorByID(opID);
      if(op == null) return;

      let jqOp = $(op.vueContext.$el);

      // Remove previous overlays
      let prevElms = jqOp.find('.stepInfoOverlay');
      prevElms.each(function() {$(this).remove();})

      let newEl = $.parseHTML("<div class='stepInfoOverlay'><b>" + (undo != null ? (undo ? "Undo ": "Redo ") : "") + "</b>" + getStepDescriptionForType(type) + "<div class='arrow'><span></span></div></div>");
      let newJqEl = $(newEl);

      jqOp.append(newEl);

      newJqEl.css("top", -(newJqEl.height() + 10 + 3));
      newJqEl.addClass("visible");
      if(prevElms.length > 0) newJqEl.addClass("stepInfoOverlayFastTrans");

      // Schedule removal
      setTimeout(function() {
        newJqEl.removeClass("stepInfoOverlayFastTrans visible").delay(500).queue(function() { $(this).remove(); });
      }, 1500);
    },

    async undoPendingUpdates(updateIDs) {
      await this.$refs.historyGraph.undoPendingUpdateEvents(updateIDs);
    },

    onRewindStatusUpdate(rewindStatus) {
      this._setRewindStatus(rewindStatus);
    },

    onHistoryGraphUpdate(updates) {
      for(let update of updates) {
        this.$refs.historyGraph.updateBranchData(update["branchID"], update["startTime"], update["endTime"], update["stepCount"], update["stepOffset"], true);
      }
    },

    onPipelineUpdateRegistered(updateIDs, branchID, stepID, stepTime) {
      this.$refs.historyGraph.assignPipelineUpdates(branchID, stepID, stepTime, updateIDs);
    },

    onHistorySplit(newBranchID, parentBranchID, splitTime, splitStepID) {
      this.$refs.historyGraph.onBranchSplit(newBranchID, parentBranchID, splitTime, splitStepID);
    },

    onReceiveProvenanceQueryResult(data) {
      if(this.$refs.provInspector) this.$refs.provInspector.onReceiveQueryResult(data);
    },

    _onEditorHistoryEventAdded(event) {
      // Pipeline Update registration and this history event tracking are independent of each other for simplicity
      // Ideally, the server would receive all information to redo/undo specific UI events and sends them on demand
      // For now, the UI tracks all UI changes with the current updateID and executes them when instructed to

      this.$refs.editorHistory.clear();  // This ensures that we always have one event registered in case it needs update

      // Register event in dictionary with current updateID

      event.updateID = PipelineUpdateService.getUniqueUpdateID();

      this.$refs.historyGraph.registerPipelineUpdateEvent(event);

      if(event.isUIEvent()) executeEvent(EVENTS.DEBUG_UI_EVENT_REGISTERED, event);

      return true;
    },

    _onEditorEventUpdate(event) {
      //True if event can be updated, false if new event needs to be created
      return event.updateID === PipelineUpdateService.getUniqueUpdateID();
    },

    _onPipelineStatusChanged() {
      this.reset();

      this.pipelineRunning = PipelineService.isPipelineStarted();

      //Only listen for events when pipelineState is running
      if(this.$refs.editorHistory) this.$refs.editorHistory.silent = !this.pipelineRunning;
    },

    _onProvQueryExecuted(query) {
      this.$emit("provQueryExecute", query);
    },

    reset() {
      this.currentStepTime = 0;
      this.maxSteps = 0;
      this.memoryString = "Cache: 0MB | Disk: 0MB";
      this.options.max = 1;
      this.currentStepID = this.options.max; // Triggers onSliderChange??
      this.rewind = null;
      this._removeRewind();

      if(this.$refs.historyGraph) this.$refs.historyGraph.reset();
      if(this.$refs.provInspector) this.$refs.provInspector.reset();

      if(this.$refs.editorHistory) {
        this.$refs.editorHistory.clear();
        this.$refs.editorHistory.silent = true;
      }

      this.pipelineRunning = false;
      this.historyActive = false;
      this.historyPaused = false;
    }
  },

  mounted() {
    this.$refs.editorHistory.initialize(system.editor);
    this.$refs.editorHistory.silent = true;

    this.reset();

    registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, this._onPipelineStatusChanged);
    this._onPipelineStatusChanged(PipelineService.getPipelineStatus());
  }
}
</script>

<style scoped>

.controlButton {
  position: absolute;
  top: 16px;
  font-size: 20px;
}

</style>

<style>

.stepInfoOverlay {
  position: absolute;
  color: white;
  background: rgb(68, 68, 68, 0.95);
  border: 2px solid #222;
  border-radius: 8px;

  font-size: 26px;
  padding-left: 5px;
  padding-right: 5px;

  top: 0;
  left: 0;
  right: 0;
  margin: 0 auto;
  text-align: center;
  max-width: 350px;

  opacity: 0;

  transition: opacity 250ms;
}

.stepInfoOverlayFastTrans {
  transition: opacity 50ms !important;
}

.stepInfoOverlay.visible {
  opacity: 1;
}

.stepInfoOverlay .arrow {
  position: absolute;
  bottom: -5px;
  left: 0;
  right: 0;
  margin: 0 auto;
  width: 50px;
  height: 25px;
}

.stepInfoOverlay .arrow > span {
  margin: 20px 0;
  display: inline-block;
  vertical-align: middle;
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-top: 10px solid #222;
}

#pipelineDebugger .controlButton.activated {
  color:rgb(105, 192, 255);
}

#pipelineDebugger .vue-slider-disabled > .vue-slider-rail:hover,
#pipelineDebugger .vue-slider-dot-handle-disabled {
  cursor: default;
}

</style>
