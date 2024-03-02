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
                <hsc-menu-item label="Expand All" @click="toggleAllDataMonitors(true)" :sync="true" />
                <hsc-menu-item label="Collapse All" @click="toggleAllDataMonitors(false)" :sync="true" />
                <hsc-menu-item label="Focus All" @click="focusAll()" :sync="true" />
              </hsc-menu-item>
              <hsc-menu-separator/>
              <hsc-menu-item label="Save" @click="savePipeline()" :sync="true" />
              <hsc-menu-item label="Load" @click="loadPipeline()" :sync="true" />
              <hsc-menu-item label="Clear" @click="clearPipeline()" :sync="true" />
            </hsc-menu-bar-item>

            <hsc-menu-bar-item label="Settings">
              <hsc-menu-item label="Restore Pipeline" :sync="true" v-model="restorePipeline"
                             @click="onSettingToggle('restorePipeline', !restorePipeline)"
                             title="Restores last pipeline when page is loaded"/>
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
                <hsc-menu-item label="Rewind" style="display: none;">
                  <hsc-menu-item>
                    <div slot="body" style="display:flex; align-items: center;" @mouseup="$refs.historyRewindSpeedSlider.resetMouseUp()">
                      <div style="margin-right: 12px;">Speed:</div>
                      <HistoryRewindSpeedSlider ref="historyRewindSpeedSlider" @change="onDebuggerConfigChange()" style="width:100px;"/>
                    </div>
                  </hsc-menu-item>
                  <hsc-menu-item label="Use Real Step Time" style="text-align: left;" v-model="debuggerRewindUseStepTime" @click="onSettingToggle('debuggerRewindUseStepTime', !debuggerRewindUseStepTime)"
                                 title="True if the real time of the steps should be used to calculate the playback speed" :sync="true" />
                </hsc-menu-item>
              </hsc-menu-item>
            </hsc-menu-bar-item>

            <hsc-menu-bar-item label="Heatmap">
              <hsc-menu-item label="None" :sync="true" type="radio" v-model="hmValue" :value="0" @click="onHeatmapChange(0)"/>
              <hsc-menu-item label="Data Size" :sync="true" type="radio" v-model="hmValue" :value="2" @click="onHeatmapChange(2)"/>
              <hsc-menu-item label="Op Runtime" :sync="true" type="radio" v-model="hmValue" :value="3" @click="onHeatmapChange(3)"/>
            </hsc-menu-bar-item>
          </hsc-menu-bar>
        </hsc-menu-style-black>
      </div>
      <div id="startButton" @click="onStartButtonClicked()"><div class="title">Start Pipeline</div><div class="loader">Start Pipeline</div></div>
      <div><PipelineDebugger v-if="debuggerEnabled" ref="debugger" @stateChange="onDebuggerStateChange" @stepChange="onDebuggerTraversal" @requestStep="onDebuggerRequestStep"></PipelineDebugger></div>
      <div style="position: absolute; right: 12px; color:#dedede; font-size: 24px; font-weight: bold; top:6px; pointer-events: none;">StreamVizzard</div>
    </div>
    <div id="content">
      <div id="editor">
        <div id="rete" ref="rete"></div>
        <HeatmapTemplate ref="heatmap" style="position:absolute; top:10px; left: 10px;"></HeatmapTemplate>
      </div>
      <Sidebar ref="sidebar"></Sidebar>
    </div>
    <div class="modals">
      <CompilePipelineModal ref="compilePipeModal"></CompilePipelineModal>
      <PipelineSimulationModal ref="simulatePipeModal"></PipelineSimulationModal>
      <SavePipelineModal ref="savePipeModal"></SavePipelineModal>
      <LoadPipelineModal ref="loadPipeModal"></LoadPipelineModal>
    </div>
  </div>
</template>

<script>
import Rete from "rete";
import ConnectionPlugin from "rete-connection-plugin";
import VueRenderPlugin from "rete-vue-render-plugin";
import AreaPlugin from "rete-area-plugin";

import ConnectionMasteryPlugin from "rete-connection-mastery-plugin";

import C from "@/scripts/components/modules"
import {ServerConnector} from "@/scripts/ServerConnector";

import CommentPlugin from "@/plugins/rete-comment-plugin";
import ContextMenuPlugin from "@/plugins/context-menu-plugin";

import $ from 'jquery'

import UserEditorHistory from "@/components/templates/tools/editorHistory/UserEditorHistory";
import NodeTemplate from "@/components/templates/NodeTemplate";
import HeatmapTemplate from "@/components/templates/heatmap/HeatmapTemplate";
import SavePipelineModal from "@/components/templates/tools/SavePipelineModal";
import {initializeConnectionMonitor} from "@/scripts/components/monitor/ConnectionMonitor";
import {EVENTS, executeEvent, registerEvent} from "@/scripts/tools/EventHandler";
import LoadPipelineModal from "@/components/templates/tools/LoadPipelineModal";
import {createNode} from "rete-context-menu-plugin/src/utils";
import {createSaveData, getOperatorSaveData, loadOperatorFromSaveData, loadSaveData,} from "@/scripts/tools/Utils";
import Sidebar from "@/components/templates/sidebar/Sidebar";
import CompilePipelineModal from "@/components/templates/tools/CompilePipelineModal";
import {initializePipelineExporter} from "@/scripts/tools/PipelineExporter";
import PipelineDebugger from "@/components/templates/debugger/PipelineDebugger";
import {getPipelineStatus, PIPELINE_STATUS, setPipelineStatus} from "@/scripts/tools/PipelineStatus";
import HistoryMemorySlider from "@/components/templates/debugger/HistoryMemorySlider";
import HistoryRewindSpeedSlider from "@/components/templates/debugger/HistoryRewindSpeedSlider";
import PipelineSimulationModal from "@/components/templates/tools/simulation/PipelineSimulationModal";
import {initializeSystem, system} from "@/main";
import {TestUtils} from "@/scripts/tools/TestUtils";
import {
  ConnectionAddedPU,
  ConnectionRemovedPU,
  OperatorAddedPU,
  OperatorRemovedPU,
  OperatorDataUpdatedPU,
  OperatorMetaDataUpdatedPU, GenericUpdatePU
} from "@/scripts/tools/PipelineUpdates";
import {synchronizeExecution} from "@/scripts/tools/debugger/DebuggingUtils";

export default {
  name: "Main",

  components: {PipelineDebugger, CompilePipelineModal, Sidebar,
    HeatmapTemplate, SavePipelineModal, LoadPipelineModal, HistoryMemorySlider,
    HistoryRewindSpeedSlider, UserEditorHistory, PipelineSimulationModal},

  methods: {
    async init() {
      const container = document.querySelector('#rete');
      const components = C.getComponents()

      const editor = new Rete.NodeEditor('demo@0.1.0', container);
      this.editor = editor;

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
      editor.use(ContextMenuPlugin, {
        delay: 50,
        allocate(component) {
          if(component.contextPath !== undefined) return component.contextPath;
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

              await loadOperatorFromSaveData(node, getOperatorSaveData(args.node));
            },
            'Group'() {
              let nodeList = [];
              nodeList.push(node);

              editor.trigger('addcomment', ({type: 'frame', nodes: nodeList, text: "Group"}))
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
      initializePipelineExporter();

      registerDataExporter("advisorEnabled", () => {return this.advisorEnabled;}, (checked) => { this.advisorEnabled = checked; });
      registerDataExporter("debugger",
          () => {return {"enabled": this.debuggerEnabled, "memLimit": this.$refs.historyMemSlider.getMemoryLimit(),
            "storageLimit": this.$refs.historyStorageSlider.getMemoryLimit(),
            "showStepInfo": this.debuggerStepNotifications, "allowHistPrev": this.debuggerAllowHistoryPreview,
            "rewindSpeed": this.$refs.historyRewindSpeedSlider.getValue(),
            "rewindUseStepTime": this.debuggerRewindUseStepTime};},
          (data) => { this.debuggerEnabled = data["enabled"]; this.debuggerAllowHistoryPreview = data["allowHistPrev"];
            this.$refs.historyMemSlider.setMemoryLimit(data["memLimit"]);
            this.$refs.historyStorageSlider.setMemoryLimit(data["storageLimit"]);
            this.debuggerStepNotifications = data["showStepInfo"]; this.$refs.historyRewindSpeedSlider.setValue(data["rewindSpeed"]);
            this.debuggerRewindUseStepTime = data["rewindUseStepTime"]});

      registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, this.updatePipelineStartButton);
      this.updatePipelineStartButton();

      //---------------- Operator Lifecycle ----------------

      editor.onComponentCreated = function (node, component){
        node.component = component;
        node.dataMonitorEnabled = true; //Component data shared between all instances -> put data in node
        node.statsMonitorEnabled = false;
      }

      editor.on('nodecreated', node => {
        operatorLookup.set(node.id, node);

        if(canRegisterPipelineUpdate()) registerPipelineUpdate(new OperatorAddedPU(node.id, node.component.getPipelineData(node)));

        executeEvent(EVENTS.NODE_CREATE, node);
      });

      //Clear operatorLookup when node is removed
      editor.on('noderemoved', node => {
        operatorLookup.delete(node.id);

        if(editor.selected.contains(node)) {
          editor.selected.clear();
          editor.trigger("nodeSelectionCleared");
        }

        if(canRegisterPipelineUpdate()) registerPipelineUpdate(new OperatorRemovedPU(node.id));

        executeEvent(EVENTS.NODE_REMOVED, node);
      });

      editor.on('connectioncreated', con => {
        if(!("id" in con)) {
          con.id = uniqueConnectionIDCounter;
          uniqueConnectionIDCounter++;
        }

        connectionLookup.set(con.id, con);

        if(canRegisterPipelineUpdate()) registerPipelineUpdate(new ConnectionAddedPU(con));

        executeEvent(EVENTS.CONNECTION_CREATED, con);
      });

      editor.on('connectionremoved', con => {
        connectionLookup.delete(con.id);

        if(canRegisterPipelineUpdate()) registerPipelineUpdate(new ConnectionRemovedPU(con.id));

        executeEvent(EVENTS.CONNECTION_REMOVED, con);
      });

      registerEvent(EVENTS.DEBUG_UI_EVENT_REGISTERED, () => {
        if(canRegisterPipelineUpdate()) registerPipelineUpdate(new GenericUpdatePU());
      })

      editor.onOperatorDataUpdated = function(node, ctrl) {
        if(canRegisterPipelineUpdate()) registerPipelineUpdate(new OperatorDataUpdatedPU(node.id, node.component.getData(node), ctrl.key));
      }

      editor.onOperatorMetaUpdated = function(node) {
        if(canRegisterPipelineUpdate()) registerPipelineUpdate(new OperatorMetaDataUpdatedPU(node.id, node.component.getMetaData(node)));
      }

      //-----------------------------------------------------

      //----------------------- Scene -----------------------

      editor.on('translate zoom nodetranslate', (e) => {
        if(e.source === "dblclick") return false; //No double click zoom

        //Block events if the node itself has the class
        if(e.node !== undefined && e.node.vueContext.$el.classList.contains("mouseEventBlocker")) return false;

        return !hasMouseEventBlocker(); //Prevented "false" if blocker is registered
      });

      //Select other node if selecting a new one
      editor.on('nodeselect', () => {
        if(editor.selected.list.length !== 0) editor.selected.clear();

        return true;
      });

      //Clear node selection when clicking outside a node (on editor space)
      editor.on('click', () => {
        editor.selected.clear();

        editor.trigger("nodeSelectionCleared");
      });

      $(document).on('mouseenter', '.mouseEventBlocker', function(e){
        mouseEventBlocker.set(e.currentTarget , true);
      });

      $(document).on('mouseleave', '.mouseEventBlocker', function(e){
        mouseEventBlocker.delete(e.currentTarget );
      });

      window.addEventListener('beforeunload', function() {
        //Save pipeline
        localStorage.setItem("lastPipeline", createSaveData());
      }, false);

      //-----------------------------------------------------

      const engine = new Rete.Engine('demo@0.1.0');

      components.map(c => {
        editor.register(c);
        engine.register(c);
      });

      editor.view.resize();

      AreaPlugin.zoomAt(editor);

      this.$forceUpdate(); //Sometimes variables hang (undo/redo display), force reload!
    },

    compilePipeline() {
      if(getPipelineStatus() !== PIPELINE_STATUS.STOPPED) return;

      this.$refs.compilePipeModal.show();
    },

    simulatePipeline() {
      if(getPipelineStatus() !== PIPELINE_STATUS.STOPPED) return;

      this.$refs.simulatePipeModal.show();
    },

    clearPipeline() {
      for(let [,v] of operatorLookup) {
        this.editor.removeNode(v);
      }

      this.onHeatmapChange(0);

      this.editor.trigger("clear");
      executeEvent(EVENTS.CLEAR_PIPELINE, this.editor);
    },

    savePipeline() {
      this.$refs.savePipeModal.show();
    },

    loadPipeline(){
      this.$refs.loadPipeModal.show();
    },

    onStartButtonClicked() {
      let status = getPipelineStatus();

      if(status === PIPELINE_STATUS.STOPPED) {
        //Start pipeline
        for (let [,v] of operatorLookup) v.component.reset(v);

        let pipelineData = createPipelineData();

        let data = {"pipeline": pipelineData, "meta": this._getStartMetaData()};

        server.startPipeline(data);
      } else if(status === PIPELINE_STATUS.STARTED) {
        //Stop pipeline
        server.stopPipeline("");
      }
    },

    onHeatmapChange(value) {
      this.hmValue = value;

      if(value === 0) {
        if(getPipelineStatus() === PIPELINE_STATUS.STARTED) server.changeHeatmapType({"hmType": value});
        this.$refs.heatmap.hide();
      } else {
        if(getPipelineStatus() === PIPELINE_STATUS.STARTED) server.changeHeatmapType({"hmType": value});
        this.$refs.heatmap.show(this.hmValue);
      }
    },

    onDebuggerTraversal(targetBranch, targetStep) {
      if(getPipelineStatus() === PIPELINE_STATUS.STARTED)
          server.socketSend({
            "cmd": "debuggerStepChange",
            "targetStep": targetStep,
            "targetBranch": targetBranch,
          })
    },

    onDebuggerRequestStep(targetBranch, targetTime) {
      if(getPipelineStatus() === PIPELINE_STATUS.STARTED)
        server.requestDebuggerStep({
          "targetTime": targetTime,
          "targetBranch": targetBranch,
        })
    },

    onDebuggerStateChange() {
      if(getPipelineStatus() === PIPELINE_STATUS.STARTED)
        server.changeDebuggerState({
          "historyActive": this.$refs.debugger ? this.$refs.debugger.isHistoryActive() : false,
          "historyRewind":  this.$refs.debugger ? this.$refs.debugger.getRewind() : null
        });
    },

    onDebuggerConfigChange() {
      if(getPipelineStatus() === PIPELINE_STATUS.STARTED)
        server.changeDebuggerConfig({
          "enabled": this.debuggerEnabled,
          "debuggerMemoryLimit": this.$refs.historyMemSlider.getMemoryLimit(),
          "debuggerStorageLimit": this.$refs.historyStorageSlider.getMemoryLimit(),
          "historyRewindSpeed": this.$refs.historyRewindSpeedSlider.getValue(),
          "historyRewindUseStepTime": this.debuggerRewindUseStepTime
        });
    },

    toggleAllDataMonitors(show) {
      for (let [,node] of operatorLookup) {
        node.component.setDataMonitorState(node, show);
      }
    },

    focusAll() {
      AreaPlugin.zoomAt(this.editor);
    },

    onSettingToggle(settingName, value) {
      if(settingName === "advisor") {
        this.advisorEnabled = value;
        if(getPipelineStatus() === PIPELINE_STATUS.STARTED) server.toggleAdvisor({"enabled": value});
      } else if(settingName === "debugger") {
        if(this.$refs.debugger) this.$refs.debugger.reset();

        this.debuggerEnabled = value;

        if(!this.debuggerEnabled) executeEvent(EVENTS.HISTORY_STATE_CHANGED, false);

        this.onDebuggerConfigChange();
      } else if(settingName === "debuggerStepNot") {
        this.debuggerStepNotifications = value;

      } else if(settingName === "debuggerHistPrev") {
        this.debuggerAllowHistoryPreview = value;

      } else if (settingName === "debuggerRewindUseStepTime") {
        this.debuggerRewindUseStepTime = value;

        this.onDebuggerConfigChange();
      } else if(settingName === "restorePipeline") {
        this.restorePipeline = value;

        localStorage.setItem("restorePipeline", this.restorePipeline);
      }
    },

    updatePipelineStartButton() {
      let status = getPipelineStatus();

      let startBtn = $('#startButton');

      if(status === PIPELINE_STATUS.STARTING) {
        startBtn.removeClass("startHidden").addClass("disabled");
        $('#startButton > .title').text("Start Pipeline");
      } else if(status === PIPELINE_STATUS.STARTED) {
        startBtn.removeClass("startHidden").removeClass("disabled");
        $('#startButton > .title').text("Stop Pipeline");
      } else if(status === PIPELINE_STATUS.STOPPED) {
        startBtn.addClass("startHidden").removeClass("disabled");
        $('#startButton > .title').text("Start Pipeline");
      } else if(status === PIPELINE_STATUS.STOPPING) {
        startBtn.addClass("startHidden").addClass("disabled");
        $('#startButton > .title').text("Stop Pipeline");
      }

      this.pipelineStatus = getPipelineStatus();
    },

    _getStartMetaData() {
      return {
        "advisorEnabled": this.advisorEnabled,
        "heatmapType": this.hmValue,
        "debuggerEnabled": this.debuggerEnabled,
        "debuggerMemoryLimit": this.$refs.historyMemSlider.getMemoryLimit(),
        "debuggerStorageLimit": this.$refs.historyStorageSlider.getMemoryLimit(),
        "historyRewindSpeed": this.$refs.historyRewindSpeedSlider.getValue(),
        "historyRewindUseStepTime": this.debuggerRewindUseStepTime
      };
    }
    },

  computed: {
    pipelineStopped() {
      return this.pipelineStatus === PIPELINE_STATUS.STOPPED;
    }
  },

  $refs: {
    heatmap: HeatmapTemplate,
    debugger: PipelineDebugger,
    historyMemSlider: HistoryMemorySlider,
    historyStorageSlider: HistoryMemorySlider
  },

  data() {
    return {
      hmValue: 0,
      advisorEnabled: false,
      debuggerEnabled: false,
      debuggerStepNotifications: false,
      debuggerAllowHistoryPreview: false,
      debuggerRewindUseStepTime: true,
      restorePipeline: localStorage.getItem("restorePipeline") === "true",
      pipelineStatus: null,
      editor: null
    }
  },

  mounted() {
    initializeSystem(this);
    this.init();

    //Load last stored pipeline if setting is set
    if(this.restorePipeline) {
      let pipeline = localStorage.getItem("lastPipeline");
      if(pipeline !== undefined) loadSaveData(JSON.parse(pipeline));
    }

    window.testUtils = new TestUtils(this.editor);
  }
}

// ----------------------- SERVER CONNECTION -----------------------

const server = new ServerConnector(3000, 3001, onSocketReceiveData);

let reqPipelineUpdates = [];

let uniqueUpdateID = 0;
let listenPipelineChanges = true;

const _serverReceiveCommands = {};
_registerServerReceiveCommands();

function _registerServerReceiveCommands() {
  _serverReceiveCommands["opMonitorData"] = (data) => {
    for(let i = 0; i < data.ops.length; i++) {
      const entry = data.ops[i];

      const opID = entry.id;
      const opData = entry.data;
      const opError = entry.error;
      const stats = entry.stats;

      setOpData(opID, opData, opError, stats);
    }
  }

  _serverReceiveCommands["conMonitorData"] = (data) => {
    for(let i = 0; i < data.cons.length; i++) {
      executeEvent(EVENTS.CONNECTION_DATA_UPDATED, data.cons[i]);
    }
  }

  _serverReceiveCommands["msgBroker"] = (data) => {
    for(let op of data.ops) {
      let opID = op.id;

      if(operatorLookup.has(opID)) {
        const opNode = operatorLookup.get(opID);

        opNode.component.setMessageBrokerState(opNode, op.broker);
      }
    }
  }

  _serverReceiveCommands["opError"] = (data) => {
    const opID = data.op;

    if(operatorLookup.has(opID)) {
      const opNode = operatorLookup.get(opID);

      opNode.component.setError(opNode, data.error);
    }
  }

  _serverReceiveCommands["heatmap"] = (data) => {
    for(const op of data.ops) {
      if(operatorLookup.has(op.op)) {
        const opNode = operatorLookup.get(op.op);
        opNode.component.setHeatmapRating(opNode, op.rating);
      }
    }

    system.$refs.heatmap.onDataUpdate(data.min, data.max, data.steps);
  }

  _serverReceiveCommands["opAdvisorSug"] = (data) => {
    if(operatorLookup.has(data.opID)) {
      const opNode = operatorLookup.get(data.opID);
      opNode.component.setAdvisorSuggestions(opNode, data.sugs);
    }
  }

  _serverReceiveCommands["debuggerData"] = async (data) => {
    if(system.$refs.debugger) await synchronizeExecution(async () => {
      await system.$refs.debugger.updateTimeline(data["active"], data["maxSteps"],
        data["stepID"], data["branchID"],
        data["branchStartTime"], data["branchEndTime"], data["branchStepOffset"],
        data["memSize"], system.$refs.historyMemSlider.getMemoryLimit(),
        data["diskSize"], system.$refs.historyStorageSlider.getMemoryLimit(), data["rewindActive"]);});
  }

  _serverReceiveCommands["debuggerHistoryEx"] = async (data) => {
    if(system.$refs.debugger) {
      await synchronizeExecution(async () => {
        await system.$refs.debugger.onStepExecution(data.stepID, data.branchID, data.op, data.type, data.undo, data.stepTime);
      });
    }
  }

  _serverReceiveCommands["debUndoPendingPU"] = async (data) => {
    await synchronizeExecution(async () => { await system.$refs.debugger.undoPendingUpdates(data["updateIDs"]); })
  }

  _serverReceiveCommands["debRegPU"] = (data) => {
    if(system.$refs.debugger) {
      system.$refs.debugger.onPipelineUpdateRegistered(data["updateIDs"], data["branchID"], data["stepID"], data["stepTime"]);
    }
  }

  _serverReceiveCommands["debReqStep"] = (data) => {
    if(system.$refs.debugger) {
      system.$refs.debugger.onReceiveRequestedStep(data["branchID"], data["stepID"]);
    }
  }

  _serverReceiveCommands["debSplit"] = (data) => {
    if(system.$refs.debugger) {
      system.$refs.debugger.onHistorySplit(data.branchID, data.parentID, data.splitTime, data.splitStep);
    }
  }

  _serverReceiveCommands["debHGUpdate"] = (data) => {
    if(system.$refs.debugger) {
      system.$refs.debugger.onHistoryGraphUpdate(data["updates"]);
    }
  }

  _serverReceiveCommands["triggerBP"] = async (data) => {
    if(system.$refs.debugger) {
      await synchronizeExecution(async () => {
        await system.$refs.debugger.onStepExecution(data.stepID, data.op, data.type, null);

        let op = operatorLookup.get(data.op);
        if(!operatorLookup.has(data.op)) return;
        op.vueContext.setBreakpointTriggered(data.bpIndex);
      });
    }
  }

  _serverReceiveCommands["status"] = (data) => {
    let status = data.status;

    if(status === "starting") {
      setPipelineStatus(PIPELINE_STATUS.STARTING);
    } else if(status === "started") {
      setPipelineStatus(PIPELINE_STATUS.STARTED);
    } else if(status === "stopping") {
      setPipelineStatus(PIPELINE_STATUS.STOPPING);
    }  else if(status === "stopped") {
      setPipelineStatus(PIPELINE_STATUS.STOPPED);
    }
  }
}

async function onSocketReceiveData(data) {
  if(data.cmd in _serverReceiveCommands) await _serverReceiveCommands[data.cmd](data);
}

window.setInterval(() => {
  if(getPipelineStatus() === PIPELINE_STATUS.STARTED) {
    if (reqPipelineUpdates.length > 0) {
      const copy = reqPipelineUpdates;
      let updateID = uniqueUpdateID;

      reqPipelineUpdates = [];
      uniqueUpdateID++;

      const updateData = [];
      for(let u of copy) updateData.push(u.createSocketData());

      sendPipelineUpdates(updateData, updateID);
    }
  } else {
    reqPipelineUpdates = [];
    uniqueUpdateID = 0;
  }
}, 250);

function canRegisterPipelineUpdate() { return getPipelineStatus() === PIPELINE_STATUS.STARTED && listenPipelineChanges; }

function registerPipelineUpdate(update) {
  if(reqPipelineUpdates.length > 0) {
    const lastElm = reqPipelineUpdates[reqPipelineUpdates.length - 1];
    if(lastElm.checkUpdate(update)) return;
  }

  reqPipelineUpdates.push(update);
}

function sendPipelineUpdates(updateData, updateID) {
  const data = {};
  data["updates"] = updateData;
  data["cmd"] = "pipelineUpdate";
  data["updateID"] = updateID;

  server.socketSend(data);
}

export function sendPipelineCompile(compileData) {
  if(getPipelineStatus() !== PIPELINE_STATUS.STOPPED) return;

  server.compile(createPipelineData(), compileData);
}

export function sendPipelineSimulate(simulateData) {
  if(getPipelineStatus() !== PIPELINE_STATUS.STOPPED) return;

  for (let [,v] of operatorLookup) v.component.reset(v);

  server.simulate(createPipelineData(), simulateData, system._getStartMetaData());
}

export function listenForPipelineChanges(listen) { listenPipelineChanges = listen; }

// ----------------------- ------------------------- ---------------

function createPipelineData() {
  const data = {
    operators: []
  };

  for (const [,v] of operatorLookup) {
    data.operators.push(v.component.getPipelineData(v));
  }

  return data;
}

function setOpData(opID, opData, opError, stats) {
  if(operatorLookup.has(opID)) {
    const opNode = operatorLookup.get(opID);

    opNode.component.setValue(opNode, opData);
    opNode.component.setError(opNode, opError);
    if(stats != null) opNode.component.setStats(opNode, stats);
  }
}

export function hasMouseEventBlocker() {
  return mouseEventBlocker.size > 0;
}

export function getOperatorByID(opID) {
  if(operatorLookup.has(opID)) return operatorLookup.get(opID);
  return null;
}

export const operatorLookup = new Map();
export const connectionLookup = new Map();

export let uniqueConnectionIDCounter = 0;

export function getUniqueUpdateID() { return uniqueUpdateID; }

// Contains elements that block (consume) translate, zoom events
export const mouseEventBlocker = new Map();

// ----------------------- DATA EXPORT -----------------------

// Contains elements that need to export / import data when saving the pipeline
const dataExporters = new Map();

export function registerDataExporter(key, getFunction, setFunction) {
  dataExporters.set(key, {"getData": getFunction, "setData": setFunction});
}

export function getDataExporter() {
  return dataExporters.entries()
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

  border-bottom: 2px solid #dedede;
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
  background: #444;
  color:white;
  height:30px;
  padding: 6px 2px 0;
  position:absolute;
  left:330px;
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
  -webkit-box-shadow: inset 0 0 5px #444;
  -moz-box-shadow: inset 0 0 5px #444;
  box-shadow: inset 0 0 5px #444;
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
  background-color: #444 !important;
  text-align: left;
}

#pageMenu .menuitem {
  font-weight: normal;
}

.menubaritem .disabled {
  pointer-events: none;
  opacity: 0.5;
}
</style>
