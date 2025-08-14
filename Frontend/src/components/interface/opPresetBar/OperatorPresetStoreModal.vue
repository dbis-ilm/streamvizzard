<template>

  <modal name="storeOperatorPresetModal" transition="pop-out" @opened="_onStoreModalOpened" :classes="'modal'" :width="300" height="auto">
    <div ref="container" :class="(loading ? ' loading' : '')" style="padding:10px;">
      <div><b>{{editMode ? 'Edit' : 'Store'}} Operator Preset</b></div>

      <div style="margin-top:10px; width: calc(100% - 6px);">
        <input type="text" class="formInputField" v-model="storeConfigName" placeholder="Preset name..." style="width: 100%;">
        <textarea class="formInputField presetDescriptionInput" v-model="storeConfigDescription" placeholder="Preset description..." style="margin-top: 10px;"/>
        <input type="text" class="formInputField" v-model="storeConfigCategory" placeholder="Preset category..." style="width: 100%; margin-top: 10px;">
      </div>

      <div style="margin-top: 10px;" v-show="!editMode">
        <SearchSelectList ref="overrideList" v-slot="{data}" :categoryRetriever="(elm) => {return elm['category']}" :descriptor="'name'"
                          :maxContentHeight="'250px'" :allowDelete=false @onSelect="_selectConfigOverride">
          <div class="limitedText" style="padding: 1px 1.1rem;">{{data["name"]}}</div>
        </SearchSelectList>
      </div>

      <div v-if="errorMessage.length > 0" class="errorContainer">{{errorMessage}}</div>

      <div class="modalFooterButtons">
        <ButtonSec :label="'Close'" @click="closeStoreModal"/>
        <ButtonSec :label="'Save'" :class="storeConfigName.trim().length > 0 ? '' : 'disabled'" @click="_confirmStoreModal"/>
      </div>
    </div>

    <NotificationModal :modalName="'opStorageConfirmModal'"></NotificationModal>
  </modal>

</template>

<script>

import NotificationModal from "@/components/interface/elements/base/NotificationModal.vue";
import SearchSelectList from "@/components/interface/elements/base/SearchSelectList.vue";
import ButtonSec from "@/components/interface/elements/base/ButtonSec.vue";
import {system} from "@/main";
import {NetworkService} from "@/scripts/services/network/NetworkService";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";

export default {
  name: "OperatorPresetStoreModal",
  components: {ButtonSec, SearchSelectList, NotificationModal},
  data() {
    return {
      loading: false,
      errorMessage: "",

      editMode: false,

      storeOp: null,
      storeOpData: null, // Filled if edit mode
      storeConfigName: "",
      storeConfigDescription: "",
      storeConfigCategory: "",

      presetList: [],
      presetUpdateCallback: null,
    }
  },
  methods: {
    openStoreModal(opNode, presetList, presetUpdateCallback) {
      this.storeOp = opNode;
      this.storeConfigName = opNode.viewName;
      this.storeConfigDescription = "";
      this.storeConfigCategory = "";
      this.presetList = presetList;
      this.presetUpdateCallback = presetUpdateCallback;
      this.editMode = false;

      this.$modal.show("storeOperatorPresetModal");
    },

    openEditModal(opData, presetList, presetUpdateCallback) {
      this.storeOp = null;
      this.storeOpData = opData;
      this.storeConfigName = opData["name"];
      this.storeConfigDescription = opData["descr"];
      this.storeConfigCategory = opData["category"];
      this.presetList = presetList;
      this.presetUpdateCallback = presetUpdateCallback;
      this.editMode = true;

      this.$modal.show("storeOperatorPresetModal");
    },

    closeStoreModal() {
      this.storeOp = null;
      this.$modal.hide("storeOperatorPresetModal");
    },

    _onStoreModalOpened() {
      this.errorMessage = "";
      this.$refs.overrideList.updateDataArray(this.presetList);
    },

    _confirmStoreModal() {
      this.errorMessage = "";

      this.storeConfigName = this.storeConfigName.trim()
      this.storeConfigDescription = this.storeConfigDescription != null ? this.storeConfigDescription.trim() : null;
      this.storeConfigCategory = this.storeConfigCategory != null ? this.storeConfigCategory.trim() : null;
      if(this.storeConfigCategory != null && this.storeConfigCategory.length === 0) this.storeConfigCategory = null;

      if(this.storeConfigName.length === 0) return;

      // If store mode, check if we have preset to override
      // If edit mode, same name is ok, but different name will also check

      let checkOverride = false;

      if(this.editMode && this.storeConfigName !== this.storeOpData["name"]) checkOverride = true;
      else if(!this.editMode) checkOverride = true;

      if(checkOverride && this.presetList.some(val => {return val.name === this.storeConfigName})) {
        this.$modal.show('opStorageConfirmModal', {
          title: "Override Confirmation",
          content: "Are you sure to override<br><i>" + this.storeConfigName + "</i>?",
          confirmAction: this._performStorePreset,
          cancelAction: () => this.$modal.hide('opStorageConfirmModal')});
      } else this._performStorePreset();
    },

    _performStorePreset() {
      let ths = this;
      this.loading = true;

      let opSaveData = null;

      if(this.editMode) {
        opSaveData = { ...this.storeOpData }; //Clone data
        opSaveData["name"] = this.storeConfigName;
        opSaveData["descr"] = this.storeConfigDescription;
        opSaveData["category"] = this.storeConfigCategory;
      } else {
        let zoom = system.editor.view.area.transform.k;
        let opBounds = this.storeOp.vueContext.$el.getBoundingClientRect();

        opSaveData = {
          "name": this.storeConfigName,
          "descr": this.storeConfigDescription,
          "category": this.storeConfigCategory,
          "className": this.storeOp.component.name,
          "saveData": DataExportService.getOperatorSaveData(this.storeOp),
          "width": opBounds.width / zoom,
          "height": opBounds.height / zoom
        };
      }

      NetworkService.storeOperator(opSaveData).then(function(res) {
        if(res) {
          ths.presetList = ths.presetList.filter(p => p.name !== opSaveData.name);
          ths.presetList.unshift(opSaveData);

          // Delete original conf if we edited it and changed name
          if(ths.editMode && ths.storeOpData["name"] !== opSaveData["name"]) {
            NetworkService.deleteStoredOperator(ths.storeOpData["name"]).then(function(res) {
              if(res) ths.presetList = ths.presetList.filter(p => p.name !== ths.storeOpData["name"]);

              if(ths.presetUpdateCallback != null) ths.presetUpdateCallback(ths.presetList);

              ths.closeStoreModal();
              ths.loading = false;
            });
          } else {
            if(ths.presetUpdateCallback != null) ths.presetUpdateCallback(ths.presetList);

            ths.closeStoreModal();
            ths.loading = false;
          }
        } else {
          ths.errorMessage = "Couldn't store preset!";
          ths.loading = false;
        }
      });
    },

    _selectConfigOverride(cfg) {
      this.storeConfigName = cfg.name;

      this._confirmStoreModal();
    },
  }
}
</script>

<style scoped>

.errorContainer {
  margin-top: 5px;
  color: red;
}

.presetDescriptionInput {
  width: 100%;
  resize: none;
  height: 6rem;
  min-height: 6rem;
  max-height: 10rem;
}

.loading {
  pointer-events: none;
  opacity: 0.75;
}

</style>
