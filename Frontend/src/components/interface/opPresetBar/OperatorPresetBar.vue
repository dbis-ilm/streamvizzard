<template>
  <div class="container dock" :style="opened ? 'width: 250px;' : ''">
    <div class="content" v-if="opened">
      <div class="title">Operator Presets</div>
      <hr>

      <SearchSelectList ref="opPresetList" class="storeSearchList" :descriptor="'name'" :allowEdit="true" :editTooltip="'Edit configuration'"
                        :categoryRetriever="(elm) => {return elm['category']}" v-slot="{data}" @onDelete="_deletePreset" @onEdit="_editPreset">
        <div style="cursor: grab;" class="opPresetListElm" @mousedown="_onPresetMouseDown($event, data)">
          <div class="opPresetHeader"><div class="limitedText" style="padding: 0 1.4rem;"><b>{{data["name"]}}</b></div></div>
          <div style="padding-top: 2px;"><i>{{data["descr"].length > 0 ? data["descr"] : "-"}}</i></div>
        </div>
      </SearchSelectList>

      <NotificationModal :modalName="'opPresetConfirmModal'" :xShift="0.375"></NotificationModal>
    </div>

    <div @click="_toggleWindow" :class="'openCloseButton left ' + (opened ? 'opened' : 'closed')" title="Open/Close the operator preset window">
      <i :class="'bi ' + (opened ? 'bi-caret-left-fill' : 'bi-caret-right-fill')"></i>
    </div>
</div>

</template>

<script>

import SearchSelectList from "@/components/interface/elements/base/SearchSelectList.vue";
import NotificationModal from "@/components/interface/elements/base/NotificationModal.vue";
import $ from "jquery";
import {system} from "@/main";
import {createNode} from "rete-context-menu-plugin/src/utils";
import {NetworkService} from "@/scripts/services/network/NetworkService";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";

export default{
  name: 'OperatorPresetBar',
  components: {NotificationModal, SearchSelectList},
  data() {
    return {
      opened: false,

      presetList: [], // Only loaded on start since this is high effort

      draggedPreset: null,
      currentDragElm: null,
      elementToBeCreated: null,

      catOpenState: null, // Stores the open/close state of the categories for convenience
    };
  },
  methods: {
    open() {
      if(this.opened) return;

      this.opened = true;

      this.$nextTick(() => {
        if(this.presetList.length === 0) this._fetchOperatorPresets();

        this.updateOperatorPresets(this.presetList);
      });
    },

    close() {
      if(!this.opened) return;

      this.catOpenState = this.$refs.opPresetList.categories.map((elm) => {return {"name": elm.name, "show": elm.show}});
      this.opened = false;
    },

    getPresetList() {
      return this.presetList;
    },

    updateOperatorPresets(configs) {
      // Enrich data array with style class for background color
      let finalDataArray = [];
      for(let elm of configs) {
        if(!this._fillPresetBgColor(elm)) continue;

        finalDataArray.push(elm);
      }

      this.presetList = finalDataArray;

      if(this.opened) this.$refs.opPresetList.updateDataArray(this.presetList, this.catOpenState);
    },

    _toggleWindow() {
      if(this.opened) this.close();
      else this.open();
    },

    _deletePreset(elm) {
      this.$modal.show('opPresetConfirmModal', {title: "Delete Confirmation", content: "Are you sure to delete preset<br><i>" + elm.name + "</i>?",
        confirmAction: () => this._confirmDelete(elm), cancelAction: () => this.$modal.hide('opPresetConfirmModal')});
    },

    _confirmDelete(elm) {
      let ths = this;
      let opPresetList = this.$refs.opPresetList;

      NetworkService.deleteStoredOperator(elm.name).then(function(res) {
        if(res != null) ths.updateOperatorPresets(opPresetList.dataArray.filter(p => p.name !== elm.name));

        ths.$modal.hide('opPresetConfirmModal');
      })
    },

    _editPreset(elm) {
      system.$refs.opPresetStoreModal.openEditModal(elm, this.getPresetList(), this.updateOperatorPresets);
    },

    _fillPresetBgColor(elm) {
      let component = system.editor.components.get(elm['className']);

      if(component == null) return false;

      elm.style = 'background: ' + component.bgColor + '; border: var(--node-border); border-width: 1px;';

      return true;
    },

    _fetchOperatorPresets() {
      let ths = this;
      this.$refs.opPresetList.loading = true;
      this.$refs.opPresetList.errorMessage = "";

      NetworkService.listStoredOperators().then(function(ops) {
        ths.$refs.opPresetList.loading = false;

        if(ops == null) {
          ths.$refs.opPresetList.errorMessage = "Couldn't load presets!";

          return;
        }

        ths.updateOperatorPresets(ops);
      });
    },

    // Drag-Drop-Functionality

    _onPresetMouseDown(e, elm) {
      if(e.buttons !== 1) return; // Only left click

      e.preventDefault();
      e.stopPropagation();

      this.elementToBeCreated = null; // Reset in case we dropped on non-editor

      if(this.currentDragElm != null) this.currentDragElm.remove();

      let zoom = system.editor.view.area.transform.k;
      let width = elm.width * zoom;
      let height = elm.height * zoom;

      const component = system.editor.components.get(elm.className);
      if(component == null) return;

      this.currentDragElm = document.createElement("div");
      this.currentDragElm.setAttribute("class", "opPresetDrag");
      this.currentDragElm.style.background = component.bgColor;
      this.currentDragElm.style.top = (e.clientY - height/2) + "px";
      this.currentDragElm.style.left = (e.clientX - width/2) + "px";
      this.currentDragElm.style.width = width + "px";
      this.currentDragElm.style.height = height + "px";
      document.body.appendChild(this.currentDragElm);

      this.draggedPreset = elm;
    },

    _onPresetMouseMove(e) {
      this.elementToBeCreated = null; // Reset in case we dropped on non-editor

      if (this.currentDragElm != null) {
        e.preventDefault();
        e.stopPropagation();

        let zoom = system.editor.view.area.transform.k;
        let width = this.draggedPreset.width * zoom;
        let height = this.draggedPreset.height * zoom;

        this.currentDragElm.style.top = (e.clientY - height/2) + "px";
        this.currentDragElm.style.left = (e.clientX - width/2) + "px";
      }
    },

    _onPresetMouseUp(e) {
      if(this.currentDragElm != null) {
        e.preventDefault();
        e.stopPropagation();

        this.currentDragElm.remove();

        // In case we dropped over editor we will trigger a mouseEnter and use this variable to create the elm
        this.elementToBeCreated = this.draggedPreset;

        this.currentDragElm = null;
        this.draggedPreset = null;
      }
    },

    _onEditorMouseEnter(e) {
      if(this.elementToBeCreated != null) {
        let areaRect = system.editor.view.area.el.getBoundingClientRect();

        let zoom = system.editor.view.area.transform.k;
        let width = this.elementToBeCreated.width;
        let height = this.elementToBeCreated.height;

        let xPos = (e.clientX - areaRect.left) / zoom - width/2;
        let yPos = (e.clientY - areaRect.top) / zoom - height/2;

        this._createOpNode(this.elementToBeCreated, xPos, yPos);
        this.elementToBeCreated = null;
      }
    },

    async _createOpNode(elm, xPos, yPos) {
      const component = system.editor.components.get(elm.className);

      const node = await createNode(component, {x: xPos, y: yPos});

      system.editor.addNode(node);

      await DataExportService.loadOperatorFromSaveData(node, elm.saveData);
    }
  },

  mounted() {
    $(document).mousemove(this._onPresetMouseMove);
    $(document).mouseup(this._onPresetMouseUp);

    this.$nextTick(() => {
      $(system.editor.view.area.container).mouseenter(this._onEditorMouseEnter);
    });
  }
}

</script>

<style scoped>

.container {
  max-width: 250px;
  height: 100%;
  border-right: 2px solid var(--main-border-color);
  background: var(--second-bg-color);

  position: fixed;
  left: 0;
}

.container hr {
  color: var(--main-border-color);
}

.content {
  padding: 6px 12px;
  height: 100%;
}

.title {
  font-weight: bold;
  font-size: 1.1rem;
  pointer-events: none;

  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.storeSearchList {
  display: flex;
  flex-direction: column;
  height: calc(100% - 7rem);
}

.opPresetHeader {
  background: var(--main-bg-color);
  border-radius: var(--button-border-radius);
  padding: 2px 0;
  border-bottom: 1px solid var(--main-hover-color);
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

</style>

<style>

.opPresetDrag {
  position: absolute;
  top: 0;
  left: 0;
  cursor: grab;
  width: 50px;
  height: 50px;
  opacity: 0.75;
  border: var(--node-border);
  border-radius: var(--node-border-radius);
  z-index: 10;
}

.storeSearchList .listElm .searchListEditIcon {
  display: none;
}

.storeSearchList .listElm:hover .searchListEditIcon {
  display: block;
}

</style>
