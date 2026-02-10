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
import {Services} from "@/scripts/services/Services";
import Vue from "vue";
import {MODALS} from "@/scripts/interface/Interface";

export default Vue.extend ({
  components: {NotificationModal, SearchSelectList},

  data() {
    return {
      /** @type {OperatorPreset|null}*/ draggedPreset: null,
      /** @type {HTMLElement|null}*/ currentDragElm: null,

      catOpenState: null, // Stores the open/close state of the categories for convenience
    };
  },

  computed: {
    opened() {
      return this.$streamvizzard.interface.showOpPresetBar;
    }
  },

  watch: {
    opened() {
      if(this.opened) {
        window.addEventListener("mousemove", this._onPresetMouseMove);
        window.addEventListener("mouseup", this._onPresetMouseUp);

        this.$nextTick(() => {
          if(Services.OpPresetService.presets.length === 0) {
            this.$refs.opPresetList.loading = true;
            this.$refs.opPresetList.errorMessage = "";

            // Fetches presets which triggers update callback
            Services.OpPresetService.fetchPresets().then((presets) => {
              if(!this.$refs.opPresetList) return; // Closed before finish

              this.$refs.opPresetList.loading = false;

              if(presets == null) this.$refs.opPresetList.errorMessage = "Couldn't load presets!";
            });

          } else this._updateOperatorPresets();
        });
      } else {
        this.catOpenState = this.$refs.opPresetList.categories.map((elm) => {return {"name": elm.name, "show": elm.show}});

        window.removeEventListener("mousemove", this._onPresetMouseMove);
        window.removeEventListener("mouseup", this._onPresetMouseUp);
      }
    }
  },

  methods: {
    _updateOperatorPresets() {
      if(this.opened) this.$refs.opPresetList.updateDataArray(Services.OpPresetService.presets, this.catOpenState);
    },

    _toggleWindow() {
      this.$streamvizzard.interface.showOpPresetBar = !this.$streamvizzard.interface.showOpPresetBar;
    },

    _deletePreset(elm) {
      this.$modal.show('opPresetConfirmModal', {title: "Delete Confirmation", content: "Are you sure to delete preset<br><i>" + elm.name + "</i>?",
        confirmAction: () => this._confirmDelete(elm), cancelAction: () => this.$modal.hide('opPresetConfirmModal')});
    },

    _confirmDelete(elm) {
      Services.OpPresetService.deletePreset(elm.name).then((result) => {
        if(result) this._updateOperatorPresets();

        this.$modal.hide('opPresetConfirmModal');
      });
    },

    _editPreset(elm) {
      this.$streamvizzard.interface.openModal(MODALS.OP_PRESET_EDIT, elm);
    },

    // -------------------------------------------- Drag-Drop-Functionality --------------------------------------------

    /** @param {MouseEvent} e
     * @param {OperatorPreset} elm*/
    _onPresetMouseDown(e, elm) {
      if(e.buttons !== 1) return; // Only left click

      e.preventDefault();
      e.stopPropagation();

      if(this.currentDragElm != null) this.currentDragElm.remove();

      let width = elm.width * this.$streamvizzard.editor.scale;
      let height = elm.height * this.$streamvizzard.editor.scale;

      const definition = this.$streamvizzard.modules.getOperatorDefinition(elm.saveData["definition"]);
      if(definition == null) return;

      this.currentDragElm = document.createElement("div");
      this.currentDragElm.setAttribute("class", "opPresetDrag");
      this.currentDragElm.style.background = definition.bgColor;
      this.currentDragElm.style.top = (e.clientY - height/2) + "px";
      this.currentDragElm.style.left = (e.clientX - width/2) + "px";
      this.currentDragElm.style.width = width + "px";
      this.currentDragElm.style.height = height + "px";
      document.body.appendChild(this.currentDragElm);

      this.draggedPreset = elm;
    },

    _onPresetMouseMove(e) {
      if(this.currentDragElm == null) return;

      e.preventDefault();
      e.stopPropagation();

      let zoom = this.$streamvizzard.editor.scale;
      let width = this.draggedPreset.width * zoom;
      let height = this.draggedPreset.height * zoom;

      this.currentDragElm.style.top = (e.clientY - height/2) + "px";
      this.currentDragElm.style.left = (e.clientX - width/2) + "px";
    },

    _onPresetMouseUp(e) {
      if(this.currentDragElm == null) return;

      e.preventDefault();
      e.stopPropagation();

      if(this.$streamvizzard.editor.mouseOver) {
        Services.OpPresetService.createOperatorFromPreset(this.draggedPreset, this.$streamvizzard.editor.mouseX, this.$streamvizzard.editor.mouseY);
      }

      this.currentDragElm.remove();
      this.currentDragElm = null;
      this.draggedPreset = null;
    },
  },

  mounted() {
    Services.OpPresetService.onPresetsChangeCb = () => {
      this._updateOperatorPresets();
    };
  }
})

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
  pointer-events: none;
}

.storeSearchList .listElm .searchListEditIcon {
  display: none;
}

.storeSearchList .listElm:hover .searchListEditIcon {
  display: block;
}

</style>
