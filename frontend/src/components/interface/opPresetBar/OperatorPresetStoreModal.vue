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

      <div v-if="errorMessage != null" class="errorContainer errorMsg">{{errorMessage}}</div>

      <div class="modalFooterButtons">
        <ButtonSec :label="'Close'" @click="closeModal"/>
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
import {Services} from "@/scripts/services/Services";
import {Modal, MODALS} from "@/scripts/interface/Interface";
import OperatorPreset from "@/scripts/services/opPresets/OperatorPreset";

export default {
  components: {ButtonSec, SearchSelectList, NotificationModal},

  data() {
    return {
      loading: false,
      errorMessage: null,

      /** @type SvOperator */ storeOp: null,
      /** @type OperatorPreset */ editPreset: null,

      storeConfigName: "",
      storeConfigDescription: "",
      storeConfigCategory: "",
    }
  },

  computed: {
    editMode() {
      return this.editPreset != null;
    }
  },

  methods: {
    /** @param {SvOperator} operator **/
    openStoreModal(operator) {
      this.storeOp = operator;
      this.editPreset = null;

      this.storeConfigName = operator.name;
      this.storeConfigDescription = "";
      this.storeConfigCategory = "";

      this.$modal.show("storeOperatorPresetModal");
    },

    /** @param {OperatorPreset} editPreset */
    openEditModal(editPreset) {
      this.storeOp = null;
      this.editPreset = editPreset;

      this.storeConfigName = editPreset.name;
      this.storeConfigDescription = editPreset.descr
      this.storeConfigCategory = editPreset.category;

      this.$modal.show("storeOperatorPresetModal");
    },

    closeModal() {
      this.storeOp = null;
      this.$modal.hide("storeOperatorPresetModal");
    },

    _onStoreModalOpened() {
      this.errorMessage = null;
      this.$refs.overrideList.updateDataArray(Services.OpPresetService.presets);
    },

    _confirmStoreModal() {
      this.errorMessage = null;

      this.storeConfigName = this.storeConfigName.trim()
      this.storeConfigDescription = this.storeConfigDescription != null ? this.storeConfigDescription.trim() : null;
      this.storeConfigCategory = this.storeConfigCategory != null ? this.storeConfigCategory.trim() : null;
      if(this.storeConfigCategory != null && this.storeConfigCategory.length === 0) this.storeConfigCategory = null;

      if(this.storeConfigName.length === 0) return;

      // If store mode, check if we have preset to override
      // If edit mode, same name is ok, but different name will also check

      let checkOverride = false;

      if(this.editMode && this.storeConfigName !== this.editPreset.name) checkOverride = true;
      else if(!this.editMode) checkOverride = true;

      if(checkOverride && Services.OpPresetService.presets.some(val => {return val.name === this.storeConfigName})) {
        this.$modal.show('opStorageConfirmModal', {
          title: "Override Confirmation",
          content: "Are you sure to override<br><i>" + this.storeConfigName + "</i>?",
          confirmAction: this._performStorePreset,
          cancelAction: () => this.$modal.hide('opStorageConfirmModal')});
      } else this._performStorePreset();
    },

    _performStorePreset() {
      this.loading = true;
      this.errorMessage = null;

      let newPreset = new OperatorPreset();
      newPreset.name = this.storeConfigName;
      newPreset.descr = this.storeConfigDescription;
      newPreset.category = this.storeConfigCategory;
      newPreset.width = this.editMode ? this.editPreset.width : this.storeOp.width;
      newPreset.height = this.editMode ? this.editPreset.height : this.storeOp.height;
      newPreset.saveData = this.editMode ? this.editPreset.saveData : this.storeOp.exportSaveData();

      Services.OpPresetService.storePreset(newPreset).then((storedPreset) => {
        if(storedPreset != null) {
          // Delete original conf if we edited it and changed the name
          if(this.editMode && this.editPreset.name !== newPreset.name) {
            Services.OpPresetService.deletePreset(this.editPreset.name).then();
          }

          this.editPreset = newPreset;

          this.closeModal();

        } else this.errorMessage = "Couldn't store preset!";

        this.$modal.hide('opStorageConfirmModal');
      });

      this.loading = false;
    },

    _selectConfigOverride(cfg) {
      this.storeConfigName = cfg.name;

      this._confirmStoreModal();
    },
  },

  mounted() {
    this.$streamvizzard.interface.registerModal(new Modal(MODALS.OP_PRESET_STORE, this.openStoreModal, this.closeModal));
    this.$streamvizzard.interface.registerModal(new Modal(MODALS.OP_PRESET_EDIT, this.openEditModal, this.closeModal));
  }
}
</script>

<style scoped>

.errorContainer {
  margin-top: 5px;
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
