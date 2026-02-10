<template>
<div id="pipelineDebugger" style="width: 30%; margin: 0 auto; display:inline-block; position: relative;">
  <EditorHistory ref="editorHistory" :onEventAdded="_onEditorHistoryEventAdded" :canUpdateEvent="_onEditorEventUpdate" :maxEvents="null" :clearRedoOnNewEvent="false"></EditorHistory>
  <div :class="['clickableIcon', 'controlButton', !historyActive && 'disabled', $streamvizzard.debugger.rewinding && !$streamvizzard.debugger.rewindForward && 'activated']"
       title="Rewind Backward" @click="_rewind(false)" style="left: -35px;"><i class="bi bi-rewind-circle"></i></div>
  <div :class="'clickableIcon controlButton ' + (!historyActive ? 'disabled' : '')" title="1 Step Backward" @click="_stepHistory(-1)" style="left: -12px;"><i class="bi bi-arrow-left-circle"></i></div>
  <div style="display: inline-block; position: relative;">
    <div style="cursor:default;">Pipeline History <i class="bi bi-info-circle" :title="memoryInfo"></i></div>
    <div :class="'clickableIcon ' + (!$streamvizzard.pipeline.isPipelineStarted() ? 'disabled' : '')" title="Toggles the history graph" @click="_toggleHistoryGraph" style="position: absolute; font-size: 26px; right: -30px; top: calc((100% - 36px)/2);"><i :class="'bi bi-diagram-2' + ($refs.historyGraph && $refs.historyGraph.isOpen ? '-fill' : '')"></i></div>
    <div v-if="$streamvizzard.debugger.provenanceEnabled" :class="'clickableIcon ' + (!$streamvizzard.pipeline.isPipelineStarted() ? 'disabled' : '')" title="Toggles the provenance inspector" @click="_toggleProvInspector" style="position: absolute; font-size: 22px; right: -56px; top: calc((100% - 29px)/2);"><i :class="'bi bi-clipboard-data' + ($refs.provInspector && $refs.provInspector.isOpen ? '-fill' : '')"></i></div>
  </div>

  <vue-slider class="stepSlider" v-model="currentStepID" :disabled="!historyActive" v-bind="options" :tooltip-formatter="val => _getStepString(val)"
              @drag-start="draggingSlider=true" @change="_onStepSliderChange" @drag-end="_onStepSliderRelease" />

  <div :class="['clickableIcon', 'controlButton', !historyActive && 'disabled']" title="1 Step Forward" @click="_stepHistory(1)" style="right: -12px;"><i class="bi bi-arrow-right-circle"></i></div>
  <div :class="['clickableIcon', 'controlButton', 'mirrorY', !historyActive && 'disabled', $streamvizzard.debugger.rewinding && $streamvizzard.debugger.rewindForward && 'activated']"
       title="Rewind Forward" @click="_rewind(true)" style="right: -35px;margin-top: 0.5px;"><i class="bi bi-rewind-circle"></i></div>
  <div :class="['clickableIcon', 'controlButton', maxSteps <= 0 && 'disabled']" title="Pause / Continue the pipeline" @click="_toggleState" style="right: -58px;"><i :class="'bi ' + (!historyActive ? 'bi-pause-circle' : 'bi-play-circle')"></i></div>
  <HistoryGraph ref="historyGraph" @onBranchTraversal="_onBranchTraversal" :traversalAllowed="historyActive && !$streamvizzard.debugger.rewinding" @onHistoryTraversal="_toggleHistoryTraversal"></HistoryGraph>
  <ProvInspector ref="provInspector" :debugger="this" v-if="$streamvizzard.debugger.provenanceEnabled"></ProvInspector>
</div>
</template>

<script>
import 'vue-slider-component/theme/antd.css'
import {EVENTS, executeEvent, registerEvent} from "@/scripts/tools/EventHandler";
import {clamp, formatDataSize, formatTime} from "@/scripts/tools/Utils";
import EditorHistory from "@/components/utils/editorHistory/EditorHistory.vue";
import HistoryGraph from "@/components/features/debugger/HistoryGraph.vue";
import ProvInspector from "@/components/features/debugger/ProvInspector.vue";
import {Services} from "@/scripts/services/Services";
import {SvInstance} from "@/scripts/StreamVizzard";

// Detailed information about the branches, their step count and offsets are stored inside the history graph for lookup!

export default {
  components: {ProvInspector, HistoryGraph, EditorHistory},

  data() {
    return {
      draggingSlider: false,

      // Controls slider, real values are defined in debugger/historyGraph
      currentStepID: 1,
      maxSteps: 0,

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

  computed: {
    historyActive() {
      return this.$streamvizzard.debugger.historyActive;
    },

    historyGraph() {
      return this.$refs.historyGraph;
    },

    memoryInfo() {
      let currentMemLimit = this.$streamvizzard.debugger.memoryLimit;
      let currentStorageLimit = this.$streamvizzard.debugger.storageLimit;

      let currentMemSize = this.$streamvizzard.debugger.currentMemSize;
      let currentStorageSize = this.$streamvizzard.debugger.currentStorageSize;

      return "Cache: " + (currentMemLimit != null ? (formatDataSize(currentMemSize) + " / " + formatDataSize(currentMemLimit)) : formatDataSize(currentMemSize))
          + " | Disk: " + (currentStorageLimit != null ? (formatDataSize(currentStorageSize) + " / " + formatDataSize(currentStorageLimit)) : formatDataSize(currentStorageSize));
    }
  },

  methods: {
    _getStepString(val) {
      if(this.maxSteps <= 0) return 'Step: 0 / 0';

      let timeStr = (this.$refs.historyGraph.isOpen ? '| ΔTime: ' + formatTime(this.$refs.historyGraph.getCurrentDeltaTime()) : '');

      return 'Step: ' + (val - this.options.min + 1) + ' / ' + this.maxSteps + timeStr;
    },

    _toggleState() {
      this.$streamvizzard.debugger.changeState(!this.historyActive, this.$streamvizzard.debugger.rewinding, this.$streamvizzard.debugger.rewindForward);
    },

    _rewind(forward) {
      let rewindActive = true;

      // Disable rewind if we select same rewind mode again
      if(this.$streamvizzard.debugger.rewinding && this.$streamvizzard.debugger.rewindForward === forward) rewindActive = false;

      this.$streamvizzard.debugger.changeState(this.historyActive, rewindActive, forward);
    },

    _onStepSliderChange() {
      this.$refs.historyGraph.signalTargetRequested(this.$refs.historyGraph.currentBranchID, this.currentStepID);

      let currentBID = this.$refs.historyGraph.currentBranchID;

      this.$streamvizzard.debugger.traverseTo(currentBID, (this.currentStepID + this.$refs.historyGraph.getStepOffsetForBranch(currentBID)))
    },

    _onStepSliderRelease() {
      this.draggingSlider = false;

      // Sync current step since we only update on traversal when not dragging
      this._syncSlider();
    },

    _onBranchTraversal(branchID, stepID, targetTime) {
      // Triggered by history graph based on available information (stepID vs stepTime)

      if(stepID != null) {
        this.$streamvizzard.debugger.traverseTo(branchID, stepID);
      } else {
        this.$streamvizzard.debugger.requestStep(branchID, targetTime, (branchID, stepID) => {
          this.$refs.historyGraph.onReceiveRequestedStep(branchID, stepID);
        });
      }
    },

    _syncSlider(syncStep=true) {
      // Synchronizes the current slider state with the selected step/branch from the graph

      let bd = this.$refs.historyGraph.getCurrentBranchData();

      this.maxSteps = bd.stepCount;
      this.options.max = bd.stepCount - 1;

      if(syncStep) this.currentStepID = bd.stepID - bd.offset;
    },

    _stepHistory(val) {
      this.currentStepID = clamp(this.currentStepID + val, this.options.min, this.options.max);

      this._onStepSliderChange();
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
        Services.PipelineUpdates.listenForPipelineChanges(false);
        executeEvent(EVENTS.UI_HISTORY_TRAVERSE, [true, true]);
      } else {
        Services.PipelineUpdates.listenForPipelineChanges(true);
        executeEvent(EVENTS.UI_HISTORY_TRAVERSE, [false, true]);
      }
    },

    // ----------------------------------------------- Backend Callbacks -----------------------------------------------

    /** @param {DebugStep} currentStep
     * @param {Number} maxSteps
     * @param {Number} branchStartTime
     * @param {Number} branchEndTime
     * @param {Number} branchStepOffset */
    async updateHistory(currentStep, maxSteps, branchStartTime, branchEndTime, branchStepOffset) {
      this.$refs.historyGraph.updateBranchData(currentStep.branchID, branchStartTime, branchEndTime, maxSteps, branchStepOffset);
      await this.$refs.historyGraph.setCurrentStep(currentStep.branchID, currentStep.stepID, currentStep.stepTime, true);

      this._syncSlider();
    },

    /** @param {DebugStep} step **/
    async onStepExecution(step) {
      await this.$refs.historyGraph.setCurrentStep(step.branchID, step.stepID, step.stepTime, false);

      // Only sync slider position when not currently dragging to avoid sync stuttering
      this._syncSlider(!this.draggingSlider);
    },

    async undoPendingUpdates(updateIDs) {
      await this.$refs.historyGraph.undoPendingUpdateEvents(updateIDs);
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

    // -----------------------------------------------------------------------------------------------------------------

    _onEditorHistoryEventAdded(event) {
      // Pipeline Update registration and this history event tracking are independent of each other for simplicity
      // Ideally, the server would receive all information to redo/undo specific UI events and sends them on demand
      // For now, the UI tracks all UI changes with the current updateID and executes them when instructed to

      this.$refs.editorHistory.clear();  // This ensures that we always have one event registered in case it needs update

      // Register event in dictionary with current updateID

      event.updateID = Services.PipelineUpdates.getUniqueUpdateID();

      this.$refs.historyGraph.registerPipelineUpdateEvent(event);

      if(event.isUIEvent()) executeEvent(EVENTS.DEBUG_UI_EVENT_REGISTERED, event);
    },

    _onEditorEventUpdate(event) {
      //True if event can be updated, false if new event needs to be created
      return event.updateID === Services.PipelineUpdates.getUniqueUpdateID();
    },

    reset() {
      this.maxSteps = 0;
      this.options.max = 1;
      this.currentStepID = this.options.max;

      if(this.$refs.historyGraph) this.$refs.historyGraph.reset();
      if(this.$refs.provInspector) this.$refs.provInspector.reset();

      if(this.$refs.editorHistory) {
        this.$refs.editorHistory.clear();
        this.$refs.editorHistory.silent = true;
      }
    }
  },

  mounted() {
    this.$streamvizzard.debugger.onResetCb = this.reset;
    this.$streamvizzard.debugger.onStepExecutedCb = this.onStepExecution;
    this.$streamvizzard.debugger.updateHistoryCb = this.updateHistory;
    this.$streamvizzard.debugger.undoPendingUpdatesCb = this.undoPendingUpdates;
    this.$streamvizzard.debugger.historyGraphUpdateCb = this.onHistoryGraphUpdate;
    this.$streamvizzard.debugger.pipelineUpdateRegCb = this.onPipelineUpdateRegistered;
    this.$streamvizzard.debugger.onHistorySplitCb = this.onHistorySplit;
    this.$streamvizzard.debugger.receiveProvResCb = this.onReceiveProvenanceQueryResult;

    this.$refs.editorHistory.silent = true;

    registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, () => {
      // Only listen for events when pipelineState is running
      if(this.$refs.editorHistory) this.$refs.editorHistory.silent = !SvInstance.pipeline.isPipelineStarted();
    });

  }
}
</script>

<style scoped>

.controlButton {
  position: absolute;
  top: 16px;
  font-size: 20px;
}

.stepSlider {
  display: inline-block;
  width: calc(100% - 40px) !important;
  margin-top: -0.5px
}

</style>

<style>

#pipelineDebugger .controlButton.activated {
  color:rgb(105, 192, 255);
}

#pipelineDebugger .vue-slider-disabled > .vue-slider-rail:hover,
#pipelineDebugger .vue-slider-dot-handle-disabled {
  cursor: default;
}

</style>
