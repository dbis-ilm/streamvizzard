<template>
  <div id="app">
    <div id="header">
      <UserEditorHistory ref="undoRedoManager" maxEvents="50"></UserEditorHistory>
      <div id="pageMenu" style="position: absolute; z-index:998;">
        <hsc-menu-style-black>
          <hsc-menu-bar style="border-radius: 4px; color:inherit; background: None;">
            <hsc-menu-bar-item label="Pipeline">
              <hsc-menu-item label="Undo" title="Shortcut: Ctrl + Z" @click="$refs.undoRedoManager.performUndo()"
                             :class="$refs.undoRedoManager && $refs.undoRedoManager.hasUndo() ? '' : 'disabled'" :sync="true" />
              <hsc-menu-item label="Redo" title="Shortcut: Ctrl + Y" @click="$refs.undoRedoManager.performRedo()"
                             :class="$refs.undoRedoManager && $refs.undoRedoManager.hasRedo() ? '' : 'disabled'" :sync="true" />
              <hsc-menu-separator/>
              <hsc-menu-item label="Visibility">
                <hsc-menu-item label="Auto Arrange" @click="autoArrange()" :sync="true" />
                <hsc-menu-item label="Expand All" @click="toggleAllOperators(true)" :sync="true" />
                <hsc-menu-item label="Collapse All" @click="toggleAllOperators(false)" :sync="true" />
                <hsc-menu-item label="Focus All" @click="focusAll()" :sync="true" />
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

            <hsc-menu-bar-item label="Settings">
              <hsc-menu-item label="General">
                <hsc-menu-item label="Restore Pipeline" :sync="true" v-model="restorePipeline"
                               @click="onSettingToggle('restorePipeline', !restorePipeline)"
                               title="Restores last pipeline when page is loaded"/>
              </hsc-menu-item>
              <hsc-menu-separator/>

              <hsc-menu-item label="Monitor">
                <hsc-menu-item title="If the pipeline monitor should be enabled to visualize processed data and statistics"
                               label="Enabled" v-model="monitorEnabled" @click="onSettingToggle('monitor', !monitorEnabled)" :sync="true" />
                <hsc-menu-item label="Heatmap">
                  <hsc-menu-item label="Disabled" :sync="true" type="checkbox" :checked="$refs.heatmap ? $refs.heatmap.hmType === 0 : false" @click="onHeatmapChange(0)"/>
                  <hsc-menu-item label="Data Size" :sync="true" type="checkbox" :checked="$refs.heatmap ? $refs.heatmap.hmType === 2 : false" @click="onHeatmapChange(2)"/>
                  <hsc-menu-item label="Execution Time" :sync="true" type="checkbox" :checked="$refs.heatmap ? $refs.heatmap.hmType === 3 : false" @click="onHeatmapChange(3)"/>
                </hsc-menu-item>
                <hsc-menu-item title="If detailed statistics for the operator execution should be tracked and stored. For most reliable execution results, the pipeline should be executed with the highest possible source data rates. Moreover, a longer pipeline execution duration reduces the impact of execution fluctuations."
                               label="Track Stats" v-model="monitorTrackStats" @click="onSettingToggle('monitorTrackStats', !monitorTrackStats)" :sync="true" />
              </hsc-menu-item>
              <hsc-menu-separator/>

              <hsc-menu-item label="Advisor">
                <hsc-menu-item title="If the pipeline advisor should be enabled to suggest suitable operators"
                               label="Enabled" v-model="advisorEnabled" @click="onSettingToggle('advisor', !advisorEnabled)" :sync="true" />
              </hsc-menu-item>
              <hsc-menu-separator/>

              <hsc-menu-item label="Debugger">
                <hsc-menu-item label="Enabled" v-model="debuggerEnabled" @click="onSettingToggle('debugger', !debuggerEnabled)" :sync="true" />
                <hsc-menu-item label="History">
                  <hsc-menu-item>
                  <div slot="body" style="display:flex; align-items: center;" @mouseup="$refs.historyMemSlider.resetMouseUp()">
                    <div style="margin-right: 12px; width: 90px; text-align: left;">Cache Limit:</div>
                    <HistoryMemorySlider ref="historyMemSlider" @change="onDebuggerConfigChange()" minValue="1" maxValue="64000" style="width:100px;"/>
                  </div>
                  </hsc-menu-item>
                  <hsc-menu-item>
                    <div slot="body" style="display:flex; align-items: center;" @mouseup="$refs.historyStorageSlider.resetMouseUp()">
                      <div style="margin-right: 12px; width: 90px; text-align: left;">Disk Limit:</div>
                      <HistoryMemorySlider ref="historyStorageSlider" @change="onDebuggerConfigChange()" minValue="0" maxValue="64000" style="width:100px;"/>
                    </div>
                  </hsc-menu-item>
                </hsc-menu-item>
                <hsc-menu-item label="Step Info" v-model="debuggerStepNotifications" @click="onSettingToggle('debuggerStepNot', !debuggerStepNotifications)" :sync="true"
                               title="If information about the executed steps should be displayed while manually traversing the history"/>
                <hsc-menu-item label="History Preview" v-model="debuggerAllowHistoryPreview" @click="onSettingToggle('debuggerHistPrev', !debuggerAllowHistoryPreview)" :sync="true"
                               title="If the pipeline updates in the recorded history graph can be previewed by hovering"/>
                <hsc-menu-item label="Rewind">
                  <hsc-menu-item>
                    <div slot="body" style="display:flex; align-items: center;" @mouseup="$refs.historyRewindSpeedSlider.resetMouseUp()">
                      <div style="margin-right: 12px;">Speed:</div>
                      <HistoryRewindSpeedSlider ref="historyRewindSpeedSlider" @change="onDebuggerConfigChange()" style="width:100px;"/>
                    </div>
                  </hsc-menu-item>
                  <hsc-menu-item label="Use Real Step Time" style="text-align: left;" v-model="debuggerRewindUseStepTime" @click="onSettingToggle('debuggerRewindUseStepTime', !debuggerRewindUseStepTime)"
                                 title="True if the real time of the steps should be used to calculate the playback speed" :sync="true" />
                </hsc-menu-item>
                <hsc-menu-item label="Provenance">
                  <hsc-menu-item label="Enabled" style="text-align: left;" v-model="debuggerProvenanceEnabled" @click="onSettingToggle('debuggerProvenanceEnabled', !debuggerProvenanceEnabled)"
                                 title="True if provenance information should be tracked during debugging for querying." :sync="true" />
                  <hsc-menu-item label="Await Updates" style="text-align: left;" v-model="debuggerProvAwaitUpdates" @click="onSettingToggle('debuggerProvAwaitUpdates', !debuggerProvAwaitUpdates)"
                                 title="If updating of the provenance graph should be awaited before provenance queries are executed." :sync="true" />
                </hsc-menu-item>
              </hsc-menu-item>
            </hsc-menu-bar-item>
          </hsc-menu-bar>
        </hsc-menu-style-black>
      </div>
      <div id="startButton" @click="onStartButtonClicked()"><div class="title">Start Pipeline</div><div class="loader">Start Pipeline</div>
        <i class="bi bi-info-circle pipelineError" :title="pipelineError" v-if="pipelineError != null"></i>
      </div>
      <div><PipelineDebugger v-if="debuggerEnabled" ref="debugger" @stateChange="onDebuggerStateChange" @stepChange="onDebuggerTraversal" @requestStep="onDebuggerRequestStep" @provQueryExecute="onDebuggerProvQueryExecute"></PipelineDebugger></div>
      <div id="svHeading">StreamVizzard<span id="svVersion">v{{svVersion}}</span></div>
    </div>
    <div id="content">
      <div id="editor">
        <div id="rete" ref="rete"></div>
        <HeatmapTemplate ref="heatmap" style="position:absolute; top:10px; left: 20px;"></HeatmapTemplate>
      </div>
      <Sidebar ref="sidebar"></Sidebar>
      <OperatorPresetBar ref="opPresetBar"></OperatorPresetBar>
      <CompilePipelineWindow ref="compilePipelineWindow"></CompilePipelineWindow>
    </div>
    <div class="modals">
      <PipelineSimulationModal ref="simulatePipeModal"></PipelineSimulationModal>
      <StoragePipelineModal ref="loadPipeModal"></StoragePipelineModal>
      <OperatorPresetStoreModal ref="opPresetStoreModal"></OperatorPresetStoreModal>
    </div>
  </div>
</template>

<script>
import Rete from "rete";
import ConnectionPlugin from "rete-connection-plugin";
import VueRenderPlugin from "rete-vue-render-plugin";
import AreaPlugin from "rete-area-plugin";

import ConnectionMasteryPlugin from "rete-connection-mastery-plugin";

import {NetworkService} from "@/scripts/services/network/NetworkService";

import CommentPlugin from "@/plugins/rete-comment-plugin";
import ContextMenuPlugin from "@/plugins/context-menu-plugin";

import $ from 'jquery'

import UserEditorHistory from "@/components/utils/editorHistory/UserEditorHistory";
import NodeTemplate from "@/components/pipeline/NodeTemplate.vue";
import HeatmapTemplate from "@/components/features/monitor/heatmap/HeatmapTemplate";
import {initializeConnectionMonitor} from "@/scripts/components/monitor/ConnectionMonitor";
import {EVENTS, executeEvent, registerEvent} from "@/scripts/tools/EventHandler";
import {createNode} from "rete-context-menu-plugin/src/utils";
import {
  safeVal, createConnection, valueOr,
} from "@/scripts/tools/Utils";
import Sidebar from "@/components/interface/sidebar/Sidebar";
import PipelineDebugger from "@/components/features/debugger/PipelineDebugger";
import HistoryMemorySlider from "@/components/features/debugger/HistoryMemorySlider";
import HistoryRewindSpeedSlider from "@/components/features/debugger/HistoryRewindSpeedSlider";
import PipelineSimulationModal from "@/components/features/simulator/PipelineSimulationModal";
import {initializeSystem, system} from "@/main";
import {
  ConnectionAddedPU,
  ConnectionRemovedPU,
  OperatorAddedPU,
  OperatorRemovedPU,
  OperatorDataUpdatedPU,
  OperatorMetaDataUpdatedPU, GenericUpdatePU
} from "@/scripts/services/pipelineUpdates/PipelineUpdates";
import StoragePipelineModal from "@/components/interface/modals/StoragePipelineModal.vue";
import OperatorPresetBar from "@/components/interface/opPresetBar/OperatorPresetBar.vue";
import OperatorPresetStoreModal from "@/components/interface/opPresetBar/OperatorPresetStoreModal.vue";
import CompilePipelineWindow from "@/components/features/compiler/CompilePipelineWindow.vue";
import {Services} from "@/scripts/services/Services";
import {EditorInputManager} from "@/scripts/services/EditorInputManager";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";
import {PipelineUpdateService} from "@/scripts/services/pipelineUpdates/PipelineUpdateService";
import {PipelineService, PIPELINE_STATUS} from "@/scripts/services/pipelineState/PipelineService";
import {TestUtils} from "@/scripts/tools/TestUtils";
import {AutoLayoutPipeline} from "@/scripts/tools/AutoLayoutPipeline";
import {getComponents} from "@/scripts/components/modules";
import {SV_VERSION} from "@/scripts/streamVizzard";

export default {
  name: "Main",

  components: {
    CompilePipelineWindow,
    OperatorPresetStoreModal,
    OperatorPresetBar, PipelineDebugger, Sidebar,
    HeatmapTemplate, StoragePipelineModal, HistoryMemorySlider,
    HistoryRewindSpeedSlider, UserEditorHistory, PipelineSimulationModal
  },

  methods: {
    async init() {
      let ths = this;

      const container = document.querySelector('#rete');
      const components = getComponents();

      const editor = new Rete.NodeEditor(DataExportService.getEditorVersionID(), container);
      this.editor = editor;

      editor.bind("editorZoom");

      editor.bind("nodeMonitorStateChanged"); //Component -> Node, State
      editor.bind("nodeResized");
      editor.bind("nodeSelectionCleared");

      editor.bind("onNodeSocketsChanged"); //Node
      editor.bind("onNodeDSChanged"); //Display Socket -> DisplayTemplate
      editor.bind("onNodeDTChanged"); //Display Type -> DisplayTemplate
      editor.bind("onNodeDMChanged"); //Display Mode -> DisplayTemplate
      editor.bind("onNodeDataInspectChanged"); //Data Inspect -> DisplayTemplate
      editor.bind("onNodeAdvisorChanged"); //Advisor Suggestions -> Node

      editor.use(ConnectionPlugin);
      editor.use(VueRenderPlugin, {
        component: NodeTemplate
      });

      let opPresetStoreModal = this.$refs.opPresetStoreModal;
      let opPresetBat = this.$refs.opPresetBar;

      editor.use(ContextMenuPlugin, {
        delay: 50,
        allocate(component) {
          if (component.contextPath !== undefined) return component.contextPath;
          else return ['default'];
        },
        rename(component) {
          return component.displayName;
        },
        nodeItems: node => {
          return {
            'Delete': false,
            'Clone': false,
            async 'Duplicate'(args) {
              const {name, position: [x, y], ...params} = args.node;
              const component = editor.components.get(name);
              const node = await createNode(component, {...params, x: x + 10, y: y + 10});

              editor.addNode(node);

              await DataExportService.loadOperatorFromSaveData(node, DataExportService.getOperatorSaveData(args.node));

              editor.trigger("selectnode", editor.view.nodes.get(node));
            },
            async 'Replace'(args) {
              let node = args.node;

              // Update internal mouse pos to position of current node to force new node to be placed at same position
              editor.view.area.mouse = {"x": node.position[0], "y": node.position[1]};

              let replaceNode = function(newNode) {
                // Update internal operator ID (a new opID is assigned)

                newNode.uuid = node.uuid;
                newNode.viewName = node.viewName;

                // Exchange OUT connections

                for(let [k, ] of node.outputs.entries()) {
                  let output = node.outputs.get(k);
                  let newOutput = newNode.outputs.get(k);

                  if(output == null || newOutput == null) continue;

                  for(let c of output.connections) {
                    const otherOp = c.input.node.component;
                    const otherSocket = otherOp.getSocketByKey(c.input.node, c.input.key);

                    editor.removeConnection(c);
                    createConnection(editor, newOutput, otherSocket);
                  }
                }

                // Exchange IN connections

                for(let [k, ] of node.inputs.entries()) {
                  let input = node.inputs.get(k);
                  let newInput = newNode.inputs.get(k);

                  if(input == null || newInput == null) continue;

                  for(let c of input.connections) {
                    const otherOp = c.input.node.component;
                    const otherSocket = otherOp.getSocketByKey(c.output.node, c.output.key);

                    editor.removeConnection(c);
                    createConnection(editor, otherSocket, newInput);
                  }
                }

                // Remove old node

                node.component.editor.removeNode(node);

                executeEvent(EVENTS.NODE_REPLACED, [newNode, node]);
              };

              editor.trigger("contextmenu", ({e: args.e, nodeCreatedCallback: replaceNode}));
            },
            'Group'() {
              let nodeList = [];
              nodeList.push(node);

              editor.trigger('addcomment', ({type: 'frame', nodes: nodeList, text: "Group"}))
            },
            'Store Preset'(args) {
              opPresetStoreModal.openStoreModal(args.node, opPresetBat.getPresetList(), opPresetBat.updateOperatorPresets);
            }
          }
        },
      });
      editor.use(AreaPlugin);
      editor.use(CommentPlugin, {
        margin: 40
      });
      editor.use(ConnectionMasteryPlugin);

      this.$refs.heatmap.initialize(editor, false);
      this.$refs.sidebar.initialize(editor, this);
      this.$refs.undoRedoManager.initialize(editor);

      initializeConnectionMonitor(editor);

      Services.initialize();

      DataExportService.registerDataExporter("interface", () => {
        return {"sidebarOpened": this.$refs.sidebar.opened}
      }, (data) => {
        this.$refs.sidebar.opened = data["opened"]
      })
      DataExportService.registerDataExporter("advisor", () => {
        return {"enabled": this.advisorEnabled};
      }, (data) => {
        this.advisorEnabled =  safeVal(data["enabled"], this.advisorEnabled);
      });
      DataExportService.registerDataExporter("monitor", () => {
            return {
              "enabled": this.monitorEnabled,
              "trackStats": this.monitorTrackStats
            }
          },
          (data) => {
            this.monitorEnabled = safeVal(data["enabled"], this.monitorEnabled);
            this.monitorTrackStats = safeVal(data["trackStats"], this.monitorTrackStats);
          });
      DataExportService.registerDataExporter("debugger",
          () => {
            return {
              "enabled": this.debuggerEnabled,
              "memLimit": this.$refs.historyMemSlider.getMemoryLimit(),
              "storageLimit": this.$refs.historyStorageSlider.getMemoryLimit(),
              "showStepInfo": this.debuggerStepNotifications,
              "allowHistPrev": this.debuggerAllowHistoryPreview,
              "rewindSpeed": this.$refs.historyRewindSpeedSlider.getValue(),
              "rewindUseStepTime": this.debuggerRewindUseStepTime,
              "debuggerProvenanceEnabled": this.debuggerProvenanceEnabled,
              "debuggerProvAwaitUpdates": this.debuggerProvAwaitUpdates
            };
          },
          (data) => {
            this.debuggerEnabled = safeVal(data["enabled"], this.debuggerEnabled);
            this.debuggerAllowHistoryPreview = safeVal(data["allowHistPrev"], this.debuggerAllowHistoryPreview);
            this.$refs.historyMemSlider.setMemoryLimit(safeVal(data["memLimit"], this.$refs.historyMemSlider.getMemoryLimit()));
            this.$refs.historyStorageSlider.setMemoryLimit(safeVal(data["storageLimit"], this.$refs.historyStorageSlider.getMemoryLimit()));
            this.debuggerStepNotifications = safeVal(data["showStepInfo"], this.debuggerStepNotifications);
            this.$refs.historyRewindSpeedSlider.setValue(safeVal(data["rewindSpeed"], this.$refs.historyRewindSpeedSlider.getValue()));
            this.debuggerRewindUseStepTime = safeVal(data["rewindUseStepTime"], this.debuggerRewindUseStepTime);
            this.debuggerProvenanceEnabled = safeVal(data["debuggerProvenanceEnabled"], this.debuggerProvenanceEnabled);
            this.debuggerProvAwaitUpdates = safeVal(data["debuggerProvAwaitUpdates"], this.debuggerProvAwaitUpdates);
          });

      registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, this.updatePipelineStartButton);
      this.updatePipelineStartButton();

      // Override modal show function
      let showOverride = this.$modal.show;
      this.$modal.show = function (modalName, params) {
        executeEvent(EVENTS.MODAL_OPENED, modalName);
        showOverride(modalName, params);
      }

      //---------------- Operator Lifecycle ----------------

      editor.onComponentCreated = function (node, component) {
        node.component = component;
        node.dataMonitorEnabled = true;
        node.settingsEnabled = true;
      }

      editor.on('nodecreated', node => {
        PipelineService.registerOperator(node.id, node);

        ths.onPipelineUpdated(new OperatorAddedPU(node.id, node.component.getPipelineData(node)));

        executeEvent(EVENTS.NODE_CREATE, node);
      });

      //Clear operatorLookup when node is removed
      editor.on('noderemoved', node => {
        PipelineService.deleteOperator(node.id);

        if (editor.selected.contains(node)) {
          editor.selected.clear();
          editor.trigger("nodeSelectionCleared");
        }

        ths.onPipelineUpdated(new OperatorRemovedPU(node.id));

        executeEvent(EVENTS.NODE_REMOVED, node);
      });

      editor.on('connectioncreated', con => {
        PipelineService.registerConnection(con);

        ths.onPipelineUpdated(new ConnectionAddedPU(con));

        executeEvent(EVENTS.CONNECTION_CREATED, con);
      });

      editor.on('connectionremoved', con => {
        PipelineService.deleteConnection(con.id);

        ths.onPipelineUpdated(new ConnectionRemovedPU(con.id));

        executeEvent(EVENTS.CONNECTION_REMOVED, con);
      });

      registerEvent(EVENTS.DEBUG_UI_EVENT_REGISTERED, () => {
        ths.onPipelineUpdated(new GenericUpdatePU());
      })

      editor.onOperatorDataUpdated = function (node, ctrl) {
        ths.onPipelineUpdated(new OperatorDataUpdatedPU(node.id, node.uuid, node.component.getData(node), ctrl.key));
      }

      editor.onOperatorMetaUpdated = function (node) {
        ths.onPipelineUpdated(new OperatorMetaDataUpdatedPU(node.id, node.component.getMetaData(node)));
      }

      //-----------------------------------------------------

      //----------------------- Scene -----------------------

      editor.on('translate zoom nodetranslate', (e) => {
        if (e.source === "dblclick") return false; //No double click zoom

        // Resize adds a flag to the node
        if (e.node !== undefined && e.node.isResized === true) return false;

        if (EditorInputManager.hasSelectedInput()) return false;

        if (e.zoom !== undefined) editor.trigger("editorZoom", e);

        return true;
      });

      editor.on('nodeselect', () => {
        //Deselect other node if selecting a new one
        if (editor.selected.list.length !== 0) editor.selected.clear();

        return true;
      });

      //Clear node selection when clicking outside a node (on editor space)
      editor.on('click', () => {
        editor.selected.clear();

        editor.trigger("nodeSelectionCleared");
      });

      window.addEventListener('beforeunload', function () {
        //Save pipelineState
        localStorage.setItem("lastPipeline", DataExportService.createSaveData());
      }, false);

      //-----------------------------------------------------

      components.map(c => {
        editor.register(c);
      });

      editor.view.resize();

      AreaPlugin.zoomAt(editor);

      this.$forceUpdate(); //Sometimes variables hang (undo/redo display), force reload!
    },

    compilePipeline() {
      if (!PipelineService.isPipelineStopped()) return;

      this.$refs.sidebar.show();
      this.$refs.opPresetBar.close();
      this.pipelineError = null;
      this.onHeatmapChange(0);

      this.$refs.compilePipelineWindow.show();
    },

    simulatePipeline() {
      if (!PipelineService.isPipelineStopped()) return;

      this.$refs.simulatePipeModal.show();
    },

    clearPipeline() {
      for (let v of PipelineService.getAllOperators()) {
        this.editor.removeNode(v);
      }

      this.onHeatmapChange(0);

      this.pipelineError = null;

      this.editor.trigger("clear");
      executeEvent(EVENTS.CLEAR_PIPELINE, this.editor);
    },

    savePipeline() {
      this.$refs.loadPipeModal.show(false);
    },

    loadPipeline() {
      this.$refs.loadPipeModal.show(true);
    },

    onStartButtonClicked() {
      if (PipelineService.isPipelineStopped()) {
        //Start pipelineState
        for (let v of PipelineService.getAllOperators()) v.component.reset(v);

        let pipelineData = PipelineService.createPipelineData();

        let data = {"pipeline": pipelineData, "meta": this.getStartMetaData()};

        this.pipelineError = null;

        PipelineService.setPipelineStatus(PIPELINE_STATUS.STARTING);

        NetworkService.startPipeline(data).then((res) => {
          if ((res === null || !res["res"]) && PipelineService.isPipelineStarting()) PipelineService.setPipelineStatus(PIPELINE_STATUS.STOPPED);

          this.pipelineError = res?.error;
        });
      } else if (PipelineService.isPipelineStarted()) {
        //Stop pipelineState
        NetworkService.stopPipeline("");
      }
    },

    // ---- Monitor ---- TODO: Move into separate modules? (including save/load data/props)

    onHeatmapChange(value) {
      if (value === 0) this.$refs.heatmap.hide();
      else this.$refs.heatmap.show(value);

      this.onMonitorConfigChange();
    },

    onMonitorConfigChange() {
      if (PipelineService.isPipelineStarted()) NetworkService.changeMonitorConfig(this.getMonitorConfig());
    },

    getMonitorConfig() {
      return {
        "enabled": this.monitorEnabled,
        "trackStats": this.monitorTrackStats,
        "heatmapType": this.$refs.heatmap.hmType
      };
    },

    // ---- Advisor ----

    onAdvisorConfigChange() {
      if (PipelineService.isPipelineStarted()) NetworkService.changeAdvisorConfig(this.getAdvisorConfig())
    },

    getAdvisorConfig() {
      return {
        "enabled": this.advisorEnabled,
      }
    },

    // ---- Debugger ----

    onDebuggerTraversal(targetBranch, targetStep) {
      if (PipelineService.isPipelineStarted())
        NetworkService.socketSend({
          "cmd": "debuggerStepChange",
          "targetStep": targetStep,
          "targetBranch": targetBranch,
        })
    },

    onDebuggerRequestStep(targetBranch, targetTime) {
      if (PipelineService.isPipelineStarted()) {
        NetworkService.requestDebuggerStep({
          "targetTime": targetTime,
          "targetBranch": targetBranch,
        }).then(function (data) {
          if (system.$refs.debugger) system.$refs.debugger.onReceiveRequestedStep(data["branchID"], data["stepID"]);
        });
      }
    },

    onDebuggerStateChange() {
      if (PipelineService.isPipelineStarted())
        NetworkService.changeDebuggerState({
          "historyActive": this.$refs.debugger ? this.$refs.debugger.isHistoryActive() : false,
          "historyRewind": this.$refs.debugger ? this.$refs.debugger.getRewind() : null
        });
    },

    onDebuggerConfigChange() {
      if (PipelineService.isPipelineStarted()) NetworkService.changeDebuggerConfig(this.getDebuggerConfig());
    },

    getDebuggerConfig() {
      return {
        "enabled": this.debuggerEnabled,
        "debuggerMemoryLimit": this.$refs.historyMemSlider.getMemoryLimit(),
        "debuggerStorageLimit": this.$refs.historyStorageSlider.getMemoryLimit(),
        "historyRewindSpeed": this.$refs.historyRewindSpeedSlider.getValue(),
        "historyRewindUseStepTime": this.debuggerRewindUseStepTime,
        "provenanceEnabled": this.debuggerProvenanceEnabled,
        "provenanceAwaitUpdates": this.debuggerProvAwaitUpdates
      };
    },

    onDebuggerProvQueryExecute(query) {
      if (PipelineService.isPipelineStarted())
        NetworkService.executeProvenanceQuery(query);
    },

    // -----------------------

    toggleAllOperators(show) {
      for (let node of PipelineService.getAllOperators()) {
        node.component.setDataMonitorState(node, show);
        node.component.setOperatorSettingsState(node, show);
      }
    },

    focusAll() {
      AreaPlugin.zoomAt(this.editor);
    },

    async autoArrange() {
      let autoLayout = new AutoLayoutPipeline(this.editor);

      await autoLayout.layout({
        'elk.spacing.nodeNode': 75,
        'elk.layered.spacing.nodeNodeBetweenLayers': 75
      });

      this.focusAll();
    },

    onPipelineUpdated(pipelineUpdate) {
      this.pipelineError = null;

      PipelineUpdateService.registerPipelineUpdate(pipelineUpdate);
    },

    onSettingToggle(settingName, value) {
      if (settingName === "monitor") {
        this.monitorEnabled = value;

        this.onMonitorConfigChange();
      } else if (settingName === "monitorTrackStats") {
        this.monitorTrackStats = value;

        this.onMonitorConfigChange();
      } else if (settingName === "advisor") {
        this.advisorEnabled = value;

        this.onAdvisorConfigChange();
      } else if (settingName === "debugger") {
        if (this.$refs.debugger) this.$refs.debugger.reset();

        this.debuggerEnabled = value;

        if (!this.debuggerEnabled) executeEvent(EVENTS.HISTORY_STATE_CHANGED, false);

        this.onDebuggerConfigChange();
      } else if (settingName === "debuggerStepNot") {
        this.debuggerStepNotifications = value;

      } else if (settingName === "debuggerHistPrev") {
        this.debuggerAllowHistoryPreview = value;

      } else if (settingName === "debuggerRewindUseStepTime") {
        this.debuggerRewindUseStepTime = value;

        this.onDebuggerConfigChange();
      } else if (settingName === "debuggerProvenanceEnabled") {
        this.debuggerProvenanceEnabled = value;

        this.onDebuggerConfigChange();
      } else if (settingName === "debuggerProvAwaitUpdates") {
        this.debuggerProvAwaitUpdates = value;

        this.onDebuggerConfigChange();
      } else if (settingName === "restorePipeline") {
        this.restorePipeline = value;

        localStorage.setItem("restorePipeline", this.restorePipeline);
      }
    },

    updatePipelineStartButton() {
      let startBtn = $('#startButton');

      if (PipelineService.isPipelineStarting()) {
        startBtn.removeClass("startHidden").addClass("disabled");
        $('#startButton > .title').text("Start Pipeline");
      } else if (PipelineService.isPipelineStarted()) {
        startBtn.removeClass("startHidden").removeClass("disabled");
        $('#startButton > .title').text("Stop Pipeline");
      } else if (PipelineService.isPipelineStopped()) {
        startBtn.addClass("startHidden").removeClass("disabled");
        $('#startButton > .title').text("Start Pipeline");
      } else if (PipelineService.isPipelineStopping()) {
        startBtn.addClass("startHidden").addClass("disabled");
        $('#startButton > .title').text("Stop Pipeline");
      }
    },

    getStartMetaData() {
      return {
        "monitor": this.getMonitorConfig(),
        "debugger": this.getDebuggerConfig(),
        "advisor": this.getAdvisorConfig(),
      };
    }
  },

  $refs: {
    heatmap: HeatmapTemplate,
    debugger: PipelineDebugger,
    historyMemSlider: HistoryMemorySlider,
    historyStorageSlider: HistoryMemorySlider,
    opPresetBar: OperatorPresetBar,
    opPresetStoreModal: OperatorPresetStoreModal,
    compilePipelineWindow: CompilePipelineWindow,
  },

  computed: {
    pipelineStopped() {
      return PipelineService.pipelineStatus === PIPELINE_STATUS.STOPPED;
    }
  },

  data() {
    return {
      editor: null,

      // Monitor
      monitorEnabled: true,
      monitorTrackStats: false,

      // Advisor
      advisorEnabled: false,

      // Debugger
      debuggerEnabled: false,
      debuggerStepNotifications: false,
      debuggerAllowHistoryPreview: false,
      debuggerRewindUseStepTime: true,
      debuggerProvenanceEnabled: false,
      debuggerProvAwaitUpdates: false,

      // General
      pipelineError: null,
      restorePipeline: valueOr(localStorage.getItem("restorePipeline"), "true") === "true",
      compileMode: false,
      svVersion: SV_VERSION
    }
  },

  mounted() {
    initializeSystem(this);

    this.init();

    window.testUtils = new TestUtils(this.editor);

    //Load last stored pipelineState if setting is set
    if (this.restorePipeline) {
      let pipeline = localStorage.getItem("lastPipeline");
      if (pipeline !== undefined) DataExportService.loadSaveData(JSON.parse(pipeline));
    }
  }
}

</script>

<style scoped>

html, body {
  height: 100%;
  width: 100%;
}

.node .control input, .node .input-control input {
  width: 140px;
}
select, input {
  border-radius: 30px;
  background-color: white;
  padding: 2px 6px;
  border: 1px solid #999;
  font-size: 110%;
  width: 170px;
}

.connection > #pick {
  pointer-events: none!important;
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

#editor {
  height: 100%;
  flex-grow: 1;
}

#rete {
  height: 100%;
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

  -webkit-touch-callout: none; /* iOS Safari */
  -webkit-user-select: none; /* Safari */
  -khtml-user-select: none; /* Konqueror HTML */
  -moz-user-select: none; /* Old versions of Firefox */
  -ms-user-select: none; /* Internet Explorer/Edge */
  user-select: none; /* Non-prefixed version, currently supported by Chrome, Edge, Opera and Firefox */
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
  color: red;
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
