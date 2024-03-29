<template>
  <div id="sidebar">
    <div class="nodeContent" v-if="node != null">
      <div class="title">{{node.viewName}}<span class="titleID">{{node.id}}</span></div>
      <hr>
      <div class="sidebarNode">
        <div class="sidebarNodeTitle">Display Type: {{dataType}}</div>
        <div class="sidebarNodeDM">
          <div v-if="socketCount > 1" class="sidebarNodeDMSection">
            <span class="sidebarNodeDMTitle" title="The produced data of which output socket should be used to visualize">Display Socket</span>
            <v-select  ref="displaySocket" :clearable="false" :options="displaySocketOptions" class="sidebarNodeDMSelect" :value="displaySocketSelected" @input="_onDisplaySocketSwitched($event)" @dblclick.stop="" @pointermove.stop="" label="title"></v-select>
          </div>
          <div v-if="displayModeOptions.length > 0" class="sidebarNodeDMSection">
            <span class="sidebarNodeDMTitle" title="How the data produced by this operator should be visualized">Display Mode</span>
            <v-select ref="displayMode" :clearable="false" :options="displayModeOptions" class="sidebarNodeDMSelect" :value="displayModeSelected" @input="_onDisplayModeSwitched($event)" @dblclick.stop="" @pointermove.stop="" label="title"></v-select>
            <i ref="dmSettingsIcon" class="bi bi-gear sidearNodeDMSettings" title="Display Settings" @click="_onDisplayModeSettingsClicked"></i>
          </div>
          <div v-if="displayModeSettingsOpen" class="sidebarNodeDMSettings">
            <hr>
            <div ref="dmSettingContainer">
              <div v-if="displayModeSettingsEl.length === 0">No settings</div>
            </div>
            <hr>
          </div>
          <div v-if="hasInspect" class="sidebarNodeDMInspect">
            <div class="sidebarNodeDMInspectTitle">Data Inspect</div>
            <StructureInspect ref="structureInspect" class="sidebarNodeDMInspectContainer" @selected="_onInspectSwitched"></StructureInspect>
          </div>
          <div v-if="node.vueContext.errorMsg != null" class="sidebarNodeError">
            <div class="sidebarNodeErrorTitle"><b>Error</b></div>
            <div style="margin-top:5px; white-space: break-spaces">{{node.vueContext.errorMsg}}</div>
          </div>
          <div v-if="hasSuggestions" class="sidebarNodeAdvisor">
            <div class="sidebarNodeAdvisorTitle"><b>Advisions</b></div>

            <div v-for="(suggestion, index) in node.vueContext.advisorSuggestions" :key="suggestion.key" style="margin-top:5px;">
              <div><b>{{index + 1}})</b> {{suggestion.msg}}</div>
              <div v-if="suggestion.ops != null">
                <v-select :options="suggestion.ops" label="name" placeholder="Suggested Operators" :searchable="false" @input="(async function() {await _onAdvisorOperatorSelect($event)})()" :clearable="false"></v-select>
              </div>
            </div>
          </div>
          <SidebarBreakpoints ref="breakpoints" @onChange="_onBreakpointChanged"></SidebarBreakpoints>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import StructureInspect from "@/components/templates/displays/inspect/StructureInspect";
import Vue from "vue";
import SidebarBreakpoints from "@/components/templates/sidebar/SidebarBreakpoints";

export default {
  components: {SidebarBreakpoints, StructureInspect},
  name: "Sidebar",

  data() {
    return {
      editor: null,

      node: null,
      dataType: "Unknown",

      socketCount: 1,
      displayModeOptions: [],
      displayModeSelected: null,

      displayModeSettingsOpen: false,
      displayModeSettingsEl: [],

      displaySocketOptions: [],
      displaySocketSelected: null,

      hasInspect: false,

      hasSuggestions: false
    }
  },

  methods: {
    initialize(editor) {
      let elm = this;
      this.editor = editor;

      this.editor.on("nodeselect", node => {
        elm.node = node;

        elm._updateDisplayData();
        elm._onDataStructureChanged();
        elm._updateAdvisor();
        elm._updateBreakpoints();
      });

      // User UI changes
      this.editor.on("onNodeDTChanged onNodeDMChanged onNodeDSChanged", (display) => {
        if(elm.node == null || display.node.id !== elm.node.id) return;

        elm._updateDisplayData();
      });

      // User changes for example UDF, Filter
      this.editor.on("onNodeSocketsChanged", node => {
        if(elm.node == null || node.id !== elm.node.id) return;

        this._onSocketsChanged();
      });

      this.editor.on("onNodeAdvisorChanged", node => {
        if(elm.node == null || node.id !== elm.node.id) return;

        this._updateAdvisor();
      });

      this.editor.on("onNodeDataInspectChanged", display => {
        if(elm.node == null || display.node.id !== elm.node.id) return;

        this._onDataStructureChanged();
      });

      this.editor.on("nodeSelectionCleared", () => {
        elm.node = null;
        elm.hasInspect = false;
        elm.hasSuggestions = false;

        elm._toggleDisplayModeSettings(false);
      });
    },

    _updateDisplayData() {
      let dt = this.node.display.vueContext.dataType;

      if(dt !== null) {
        this.dataType = dt.displayName;

        let dm = this.node.display.vueContext.displayMode;

        // CREATE OPTIONS MENU

        this.displayModeOptions = [];

        for(let [k, v] of dt.getDisplayModes().entries()) {
          this.displayModeOptions.push({'title': v.name, 'key': k});
        }

        this.displayModeSelected = this.displayModeOptions.find(el => el.key === dm);

        //Update settings if open
        if(this.displayModeSettingsOpen) {
          this._toggleDisplayModeSettings(false);
          this._toggleDisplayModeSettings(true);
        }
      } else {
        this.dataType = "Unknown";
        this.displayModeOptions = [];
        this.displayModeSelected = null;

        this._toggleDisplayModeSettings(false);
      }

      this._onSocketsChanged();
    },

    _updateAdvisor() {
      let suggestions = this.node.vueContext.advisorSuggestions;

      this.hasSuggestions = suggestions != null;
    },

    _updateBreakpoints() {
      let elm = this;

      //Delayed load to give time for node v-if be loaded
      Vue.nextTick(function () {
        elm.$refs.breakpoints.load(elm.node.component.getBreakpoints(elm.node));
      })
    },

    _onDisplayModeSwitched(event) {
      this.displayModeSelected = event;

      this.node.display.vueContext.switchDisplayMode(event.key);

      this.$refs.displayMode.$el.blur();
    },

    _onDisplaySocketSwitched(event) {
      this.displaySocketSelected = event;

      this.node.display.vueContext.switchDisplaySocket(event.key);

      if(this.$refs.displayMode != null) this.$refs.displayMode.$el.blur();
    },

    _onDisplayModeSettingsClicked() {
      this._toggleDisplayModeSettings(!this.displayModeSettingsOpen);
    },

    _toggleDisplayModeSettings(open) {
      this.displayModeSettingsOpen = open;

      if(open) {
        this.$refs.dmSettingsIcon.classList.remove("bi-gear");
        this.$refs.dmSettingsIcon.classList.add("bi-gear-fill");

        // Add elements delayed to give time for v-if enabling

        let thiss = this;
        Vue.nextTick(function () {
          let container = thiss.$refs.dmSettingContainer;
          let settings = thiss.node.display.vueContext.getSettingsOptions();

          for (let setting of settings) {
            const componentClass = Vue.extend(setting.template);
            const instance = new componentClass({
              propsData: {
                skey: setting.key, name: setting.name, desc: setting.desc, data: setting.data,
                default: setting.default, value: setting.value, change: (key, val) => {
                  let set = thiss.node.display.vueContext.settings;
                  if (set == null) set = {};
                  set[key] = val;
                  thiss.node.display.vueContext.setSettings(set);
                }
              }
            });

            thiss.displayModeSettingsEl.push(instance);

            instance.$mount();

            container.appendChild(instance.$el);
          }
        });
      } else {
        if(this.$refs.dmSettingsIcon !== undefined) { //Make sure the icon is event visible
          this.$refs.dmSettingsIcon.classList.remove("bi-gear-fill");
          this.$refs.dmSettingsIcon.classList.add("bi-gear");
        }

        // Remove elements

        for(let i = 0; i < this.displayModeSettingsEl.length; i++) {
          let elem = this.displayModeSettingsEl[i];

          elem.$el.remove();
          elem.$destroy();
        }

        this.displayModeSettingsEl = [];
      }
    },

    _onInspectSwitched(dataInspect) {
      this.node.display.vueContext.switchDataInspect(dataInspect);
    },

    _onSocketsChanged() {
      this.socketCount = this.node.outputs.size;

      //Rebuild options
      this.displaySocketOptions = [];

      let i = 0;
      for (const [,v] of this.node.outputs.entries()) {
        this.displaySocketOptions.push({'title': v.name, 'key': i});

        i += 1;
      }

      this.displaySocketSelected = this.displaySocketOptions.find(el => el.key === this.node.display.vueContext.displaySocket);
    },

    _onDataStructureChanged() {
      let dataStructure = this.node.display.vueContext.dataStructure;

      let prevState = this.hasInspect;

      this.hasInspect = dataStructure != null;

      if(!this.hasInspect) return;

      if(!prevState) {
        //Give time to enable the component and set data in next tick if it was disabled

        let self = this;

        Vue.nextTick(function () {
          if(self.hasInspect) self.$refs.structureInspect.setStructureData(dataStructure);
        })
      } else this.$refs.structureInspect.setStructureData(dataStructure);
    },

    async _onAdvisorOperatorSelect(event) {
      // Find selected operator by path

      let paths = event.path.split("/");

      let foundComponent = null;

      for(let component of this.editor.components.values()) {
        let found = true;

        for(let i in component.path) {
          if(component.path[i] !== paths[i]) {
            found = false;
            break;
          }
        }

        if(found) {
          foundComponent = component;
          break;
        }
      }

      if(foundComponent == null) return;

      // Instantiate operator

      try {
        const node = await foundComponent.createNode();
        node.position[0] = this.node.position[0] - 60;
        node.position[1] = this.node.position[1] + 60;

        this.editor.addNode(node);
      } catch(e) {
        console.log(e);
      }
    },

    _onBreakpointChanged(bps) {
      this.node.component.setBreakpoints(this.node, bps);
    }
  }
}

</script>

<style scoped>

#sidebar {
  width: 350px;
  height: 100%;
  border-left: 2px solid #dedede;
  background: rgba(247, 247, 247, 0.7);

  cursor: default;
}

#sidebar .nodeContent {
  padding: 6px 12px;
}

#sidebar .title {
  font-weight: bold;
  font-size: 18px;
  pointer-events: none;

  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

#sidebar .titleID {
  float: right;
  position: absolute;
  right: 6px;
  font-size: 12px;
  top: 0px;
}

#sidebar hr {
  color: #dedede;
}

#sidebar .sidebarNodeTitle {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

#sidebar .sidebarNodeDM, #sidebar .sidebarNode,
#sidebar .sidebarNodeDMInspect, #sidebar .sidebarNodeDMSettings,
#sidebar .sidebarNodeAdvisor, #sidebar .sidebarNodeError {
  margin-top: 15px;
}

#sidebar .sidebarNodeDMSection {
  display: flex;
  flex-direction: row;
  height: 36px;
  margin-top: 10px;
}

#sidebar .sidebarNodeDMTitle {
  width: 110px;
  line-height: 36px;
}

#sidebar .sidebarNodeDMSelect {
  flex-grow: 1;
  margin-left: 10px;
}

#sidebar .sidearNodeDMSettings {
  width: 30px;
  font-size: 24px;
  padding-top: 1px;
  margin-left: 4px;
  cursor: pointer;
}

#sidebar .sidebarNodeDMInspectContainer {
  max-height: 400px;
  overflow-y: auto;
}

#sidebar .sidebarNodeDMInspectTitle, #sidebar .sidebarNodeAdvisorTitle, #sidebar .sidebarNodeErrorTitle {
  text-decoration: underline;
}

#sidebar .sidebarNodeAdvisor {
  padding: 10px;

  border: 1px solid red;
  border-radius: 8px;
}

.sidebarNodeAdvisorTitle {
  margin-bottom: 10px;
}

.sidebarNodeAdvisor .v-select {
  width: 250px;
  margin: 5px auto 0;
}

.sidebarNodeError {
  color: red;
}

</style>

<style>

#sidebar .sidebarNodeAdvisor, #sidebar .sidebarNodeAdvisor .vs__selected {
  color: red !important;
}
</style>
