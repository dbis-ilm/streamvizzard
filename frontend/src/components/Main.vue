<template>
  <div id="app">
    <div id="header">
      <UserEditorHistory ref="undoRedoManager" maxEvents="50"></UserEditorHistory>
      <div id="pageMenu" style="position: absolute; z-index:998;">
        <hsc-menu-style-black>
          <hsc-menu-bar style="border-radius: 4px; color:inherit; background: None;">
            <hsc-menu-bar-item label="Pipeline">
              <hsc-menu-item label="Undo" title="Shortcut: Ctrl + Z" @click="$refs.undoRedoManager.userUndo()"
                             :class="$refs.undoRedoManager && $refs.undoRedoManager.hasUndo() ? '' : 'disabled'" :sync="true" />
              <hsc-menu-item label="Redo" title="Shortcut: Ctrl + Y" @click="$refs.undoRedoManager.userRedo()"
                             :class="$refs.undoRedoManager && $refs.undoRedoManager.hasRedo() ? '' : 'disabled'" :sync="true" />
              <hsc-menu-separator/>
              <hsc-menu-item label="Operators">
                <hsc-menu-item label="Auto Arrange" @click="autoArrange()" :sync="true" />
                <hsc-menu-item label="Expand All" @click="toggleAllOperators(true)" :sync="true" />
                <hsc-menu-item label="Collapse All" @click="toggleAllOperators(false)" :sync="true" />
                <hsc-menu-item label="Fit Viewport" @click="focusAll()" :sync="true" />
              </hsc-menu-item>
              <hsc-menu-separator/>
              <hsc-menu-item label="Compile" @click="compilePipeline()" :sync="true" :class="pipelineStopped ? '' : 'disabled'"/>
              <hsc-menu-item label="Simulate" @click="simulatePipeline()" :sync="true" :class="pipelineStopped ? '' : 'disabled'">
              </hsc-menu-item>
              <hsc-menu-separator/>
              <hsc-menu-item label="Save" @click="savePipeline()" :sync="true" />
              <hsc-menu-item label="Load" @click="loadPipeline()" :sync="true" />
              <hsc-menu-item label="Clear" @click="clearPipeline()" :sync="true" />
            </hsc-menu-bar-item>

            <hsc-menu-bar-item label="Settings" :class="$streamvizzard.compiler.enabled ? 'disabled' : ''">
              <hsc-menu-item label="General">
                <hsc-menu-item label="Restore Pipeline" :sync="true" v-model="$streamvizzard.restorePipeline"
                               @click="$streamvizzard.toggleRestorePipeline(!$streamvizzard.restorePipeline)"
                               title="Restores last pipeline when page is loaded."/>
                <hsc-menu-item label="Snapping Grid" :sync="true" v-model="$streamvizzard.editor.enableSnapping"
                               title="Toggle snapping grid for dragging operations."/>
              </hsc-menu-item>
              <hsc-menu-separator/>

              <hsc-menu-item label="Monitor">
                <hsc-menu-item title="If the pipeline monitor should be enabled to visualize processed data and statistics"
                               label="Enabled" v-model="$streamvizzard.monitor.enabled" :sync="true" />
                <hsc-menu-item label="Heatmap" :checked="$streamvizzard.monitor.heatmap.isExStats()"
                               @click="$streamvizzard.monitor.heatmap.toggleExStats();" :sync="true"/>
                <hsc-menu-item title="If detailed statistics for the operator execution should be tracked and stored. For most reliable execution results, the pipeline should be executed with the highest possible source data rates. Moreover, a longer pipeline execution duration reduces the impact of execution fluctuations."
                               label="Track Stats" v-model="$streamvizzard.monitor.trackStats" :sync="true" />
              </hsc-menu-item>
              <hsc-menu-separator/>

              <hsc-menu-item label="Advisor">
                <hsc-menu-item title="If the pipeline advisor should be enabled to suggest suitable operators"
                               label="Enabled" v-model="$streamvizzard.advisor.enabled"
                               @click="$streamvizzard.advisor.toggle(!$streamvizzard.advisor.enabled)" :sync="true" />
              </hsc-menu-item>
              <hsc-menu-separator/>

              <hsc-menu-item label="Debugger">
                <hsc-menu-item label="Enabled" v-model="$streamvizzard.debugger.enabled" :sync="true" />
                <hsc-menu-item label="History">
                  <hsc-menu-item>
                  <div slot="body" style="display:flex; align-items: center;">
                    <div style="margin-right: 12px; width: 90px; text-align: left;">Cache Limit:</div>
                    <HistoryMemorySlider ref="historyMemSlider" minValue="1" maxValue="64000"
                                         v-model="$streamvizzard.debugger.memoryLimit" style="width:100px;"/>
                  </div>
                  </hsc-menu-item>
                  <hsc-menu-item>
                    <div slot="body" style="display:flex; align-items: center;">
                      <div style="margin-right: 12px; width: 90px; text-align: left;">Disk Limit:</div>
                      <HistoryMemorySlider ref="historyStorageSlider" minValue="0" maxValue="64000"
                                           v-model="$streamvizzard.debugger.storageLimit" style="width:100px;"/>
                    </div>
                  </hsc-menu-item>
                </hsc-menu-item>
                <hsc-menu-item label="Step Info" v-model="$streamvizzard.debugger.enableStepNotifications" :sync="true"
                               title="If information about the executed steps should be displayed while manually traversing the history"/>
                <hsc-menu-item label="History Preview" v-model="$streamvizzard.debugger.allowHistoryPreview" :sync="true"
                               title="If the pipeline updates in the recorded history graph can be previewed by hovering"/>
                <hsc-menu-item label="Rewind">
                  <hsc-menu-item>
                    <div slot="body" style="display:flex; align-items: center;">
                      <div style="margin-right: 12px;">Speed:</div>
                      <HistoryRewindSpeedSlider ref="historyRewindSpeedSlider" v-model="$streamvizzard.debugger.rewindSpeed" style="width:100px;"/>
                    </div>
                  </hsc-menu-item>
                  <hsc-menu-item label="Use Real Step Time" style="text-align: left;" v-model="$streamvizzard.debugger.rewindUseStepTime"
                                 title="True if the real time of the steps should be used to calculate the playback speed" :sync="true" />
                </hsc-menu-item>
                <hsc-menu-item label="Provenance">
                  <hsc-menu-item label="Enabled" style="text-align: left;" v-model="$streamvizzard.debugger.provenanceEnabled"
                                 title="True if provenance information should be tracked during debugging for querying." :sync="true" />
                  <hsc-menu-item label="Await Updates" style="text-align: left;" v-model="$streamvizzard.debugger.provAwaitUpdates"
                                 title="If updating of the provenance graph should be awaited before provenance queries are executed." :sync="true" />
                </hsc-menu-item>
              </hsc-menu-item>
            </hsc-menu-bar-item>
          </hsc-menu-bar>
        </hsc-menu-style-black>
      </div>
      <div id="startButton" @click="onStartButtonClicked()"><div class="title">Start Pipeline</div><div class="loader">Start Pipeline</div>
        <i class="bi bi-info-circle pipelineError" :title="$streamvizzard.pipeline.errorMsg" v-if="$streamvizzard.pipeline.errorMsg != null"></i>
      </div>
      <div><PipelineDebugger v-if="$streamvizzard.debugger.enabled" ref="debugger"></PipelineDebugger></div>
      <div id="svHeading">StreamVizzard<span id="svVersion">v{{$streamvizzard.version}}</span></div>
    </div>
    <div id="content">
      <EditorContainer/>
      <Sidebar/>
      <OperatorPresetBar/>
      <CompilePipelineWindow/>
    </div>
    <div class="modals">
      <PipelineSimulationModal/>
      <StoragePipelineModal/>
      <OperatorPresetStoreModal/>
    </div>
  </div>
</template>

<script>
import $ from 'jquery'

import UserEditorHistory from "@/components/utils/editorHistory/UserEditorHistory";
import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import Sidebar from "@/components/interface/Sidebar.vue";
import PipelineDebugger from "@/components/features/debugger/PipelineDebugger";
import HistoryMemorySlider from "@/components/features/debugger/HistoryMemorySlider";
import HistoryRewindSpeedSlider from "@/components/features/debugger/HistoryRewindSpeedSlider";
import PipelineSimulationModal from "@/components/features/simulator/PipelineSimulationModal";
import StoragePipelineModal from "@/components/interface/modals/StoragePipelineModal.vue";
import OperatorPresetBar from "@/components/interface/opPresetBar/OperatorPresetBar.vue";
import OperatorPresetStoreModal from "@/components/interface/opPresetBar/OperatorPresetStoreModal.vue";
import CompilePipelineWindow from "@/components/features/compiler/CompilePipelineWindow.vue";
import {PIPELINE_STATUS} from "@/scripts/pipeline/Pipeline";
import {TestUtils} from "@/scripts/tools/TestUtils";
import {AutoLayoutPipeline} from "@/scripts/tools/AutoLayoutPipeline";
import {Services} from "@/scripts/services/Services";
import {SvInstance} from "@/scripts/StreamVizzard";
import EditorContainer from "@/components/editor/EditorContainer.vue";
import {MODALS} from "@/scripts/interface/Interface";
import {HEATMAP} from "@/scripts/features/monitor/Heatmap";

export default {
  components: {
    EditorContainer,
    CompilePipelineWindow,
    OperatorPresetStoreModal,
    OperatorPresetBar, PipelineDebugger, Sidebar,
    StoragePipelineModal, HistoryMemorySlider,
    HistoryRewindSpeedSlider, UserEditorHistory, PipelineSimulationModal
  },

  methods: {
    init() {
      this.$streamvizzard.initializeSystem();

      registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, this.updatePipelineStartButton);

      this.updatePipelineStartButton();

      window.addEventListener('beforeunload', () => {
        localStorage.setItem("lastPipeline", Services.DataExporter.createSaveData());
      }, false);

      this.$forceUpdate();
    },

    compilePipeline() {
      if (!SvInstance.pipeline.isPipelineStopped()) return;

      this.$streamvizzard.interface.showSidebar = true;
      this.$streamvizzard.interface.showOpPresetBar = false;
      this.$streamvizzard.interface.closeAllModals();
      this.$streamvizzard.pipeline.errorMsg = null;

      this.$streamvizzard.monitor.heatmap.show(HEATMAP.NONE);
      this.$streamvizzard.debugger.enabled = false;

      this.$streamvizzard.compiler.startCompileMode();
    },

    simulatePipeline() {
      if (!SvInstance.pipeline.isPipelineStopped()) return;

      this.$streamvizzard.interface.openModal(MODALS.SIMULATE_PIPELINE);
    },

    clearPipeline() {
      this.$streamvizzard.pipeline.clearPipeline();
    },

    savePipeline() {
      this.$streamvizzard.interface.openModal(MODALS.STORE_PIPELINE, false);
    },

    loadPipeline() {
      this.$streamvizzard.interface.openModal(MODALS.STORE_PIPELINE, true);
    },

    onStartButtonClicked() {
      if (SvInstance.pipeline.isPipelineStopped()) {
        for (let v of SvInstance.pipeline.operators) v.resetState(); // TODO: can this be triggered with a state change listener (also need for connection!) | include errormsg, => system reset
        this.$streamvizzard.pipeline.errorMsg = null;

        let data = SvInstance.getRuntimeConfig();

        SvInstance.pipeline.setPipelineStatus(PIPELINE_STATUS.STARTING);

        Services.Network.startPipeline(data).catch((res) => {
          if(SvInstance.pipeline.isPipelineStarting()) SvInstance.pipeline.setPipelineStatus(PIPELINE_STATUS.STOPPED);

          this.$streamvizzard.pipeline.errorMsg = res?.error;
        });
      } else if (SvInstance.pipeline.isPipelineStarted()) {
        Services.Network.stopPipeline();
      }
    },

    // -----------------------

    toggleAllOperators(show) {
      for (let node of SvInstance.pipeline.operators) {
        node.showData = show;
        node.showSettings = show;
      }
    },

    focusAll() {
      SvInstance.editor.fitOperators();
    },

    async autoArrange() {
      let autoLayout = new AutoLayoutPipeline();

      await autoLayout.layout({
        'elk.spacing.nodeNode': 75,
        'elk.layered.spacing.nodeNodeBetweenLayers': 75
      });

      this.focusAll();
    },

    updatePipelineStartButton() {
      let startBtn = $('#startButton');

      if (SvInstance.pipeline.isPipelineStarting()) {
        startBtn.removeClass("startHidden").addClass("disabled");
        $('#startButton > .title').text("Start Pipeline");
      } else if (SvInstance.pipeline.isPipelineStarted()) {
        startBtn.removeClass("startHidden").removeClass("disabled");
        $('#startButton > .title').text("Stop Pipeline");
      } else if (SvInstance.pipeline.isPipelineStopped()) {
        startBtn.addClass("startHidden").removeClass("disabled");
        $('#startButton > .title').text("Start Pipeline");
      } else if (SvInstance.pipeline.isPipelineStopping()) {
        startBtn.addClass("startHidden").addClass("disabled");
        $('#startButton > .title').text("Stop Pipeline");
      }
    },
  },

  computed: {
    HEATMAP() {
      return HEATMAP
    },

    pipelineStopped() {
      return SvInstance.pipeline.pipelineStatus === PIPELINE_STATUS.STOPPED;
    }
  },

  mounted() {
    this.init();

    window.testUtils = new TestUtils();

    // Load last stored pipelineState if setting is set

    if (this.$streamvizzard.restorePipeline) {
      let pipeline = localStorage.getItem("lastPipeline");
      if (pipeline !== undefined) Services.DataExporter.loadSaveData(JSON.parse(pipeline));
    }
  }
}

</script>

<style scoped>

html, body {
  height: 100%;
  width: 100%;
}

select, input {
  border-radius: 30px;
  background-color: white;
  padding: 2px 6px;
  border: 1px solid #999;
  font-size: 110%;
  width: 170px;
}

#app {
  height: 100%;
  overflow: hidden;
}

#header {
  position: relative;
  height: 44px;

  padding-left: 5px;
  padding-right: 5px;
  padding-top: 5px;

  border-bottom: 2px solid var(--main-border-color);
}

#content {
  position: relative;
  height: calc(100% - 44px);

  display: flex;
  flex-direction: row;
}

#startButton {
  cursor:pointer;

  top:6px;
  border-radius: 6px;
  background: var(--main-font-color);
  color:white;
  height:30px;
  padding: 6px 2px 0;
  position:absolute;
  left:235px;
  width: 143px;

  user-select: none;
}

#startButton.disabled {
  opacity: 0.5;
  pointer-events: none;
}

#startButton:active {
  background: #666;
  outline: none;
  -webkit-box-shadow: inset 0 0 5px var(--main-font-color);
  -moz-box-shadow: inset 0 0 5px var(--main-font-color);
  box-shadow: inset 0 0 5px var(--main-font-color);
}

#startButton > .loader {
  position: absolute;
  opacity: 1;
  transition: opacity 0.25s;
  right: 2px;
  bottom: 8px;
  margin: 0 8px 0 0;
  width:20px;
  height:20px;
}

#startButton > .title {
  position: absolute;
  transition: margin-left 0.25s;
  left:10px;
  padding-top: 1px;
}

#startButton.startHidden > .loader {
  opacity: 0;
}

#startButton.startHidden > .title {
  margin-left: 10px;
  width: 100%;
  left:-10px;
  right:0;
}

#startButton .pipelineError {
  color: var(--error-color);
  position: absolute;
  right: 3px;
  top: 3px;
}

#svHeading {
  position: absolute;
  right: 12px;
  color:var(--main-border-color);
  font-size: 24px;
  font-weight: bold;
  top:6px;
  pointer-events: none;
  user-select: none;
}

#svHeading #svVersion {
  font-size: 0.5em;
  font-style: italic;
  padding-left: 1px;
}

</style>

<style>

#pageMenu .menubaritem {
  font-weight: bold;
  background: None !important;
}

#pageMenu .menubaritem:hover {
  font-weight: bold;
  background: None !important;
  text-decoration: underline;
}

#pageMenu .menu {
  background-color: var(--main-font-color) !important;
  text-align: left;
}

#pageMenu .menuitem {
  font-weight: normal;
}

#pageMenu .menuitem:hover {
  background-color: var(--main-hover-color) !important;
}

.menubaritem .disabled {
  pointer-events: none;
  opacity: 0.5;
}
</style>
