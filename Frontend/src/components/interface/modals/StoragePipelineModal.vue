<template>
  <modal name="loadPipelineModal" id="loadPipelineModal" transition="pop-out" @opened="() => this._selectTarget(true)" :classes="'modal'" :width="300" height="auto" :shiftX="0.1">
    <div ref="container" :class="(loadingPipeline ? ' loading' : '')" style="padding:10px;">
      <div><b>{{loadMode ? 'Load' : 'Store'}} Pipeline</b></div>

      <SwitchSelection @input="_selectTarget(serverTarget)" v-model="serverTarget"
                       :optionData="[ {'value': true, 'label': 'Server'},
                                      {'value': false, 'label': 'Disk'}]"></SwitchSelection>

      <div v-if="!loadMode" style="margin-top:10px;"><input type="text" class="formInputField" v-model="selectedPipeline" placeholder="Pipeline name..." style="width: calc(100% - 6px);"></div>

      <div class="targetContent" :style="!loadMode && !serverTarget ? 'margin-top: initial;' : ''">
        <div v-show="serverTarget">
          <SearchSelectList class="pipelineSearchList" ref="storageList" v-slot="{data}" :maxContentHeight="'250px'" @onSelect="_onPipelineClick" @onDelete="_deleteServerPipeline">
            <div class="limitedText" style="padding: 1px 1.1rem;">{{data}}</div>
          </SearchSelectList>
        </div>
        <div v-show="!serverTarget">
          <FileSelect v-if="loadMode" @input="_loadPipelineFile" extensions=".json" selectTitle="Select Pipeline"></FileSelect>
        </div>
      </div>

      <div v-if="errorMessage.length > 0" class="errorContainer">{{errorMessage}}</div>

      <div class="modalFooterButtons">
        <ButtonSec :label="'Close'" @click="hide"/>
        <ButtonSec v-if="!loadMode" :label="'Save'" :class="selectedPipeline.trim().length > 0 ? '' : 'disabled'" @click="_savePipeline"/>
      </div>
    </div>

    <NotificationModal :modalName="'storageConfirmModal'" :xShift="0.375"></NotificationModal>
  </modal>
</template>

<script>

import FileSelect from "@/components/interface/elements/base/FileSelect.vue";
import {NetworkService} from "@/scripts/services/network/NetworkService";
import ButtonSec from "@/components/interface/elements/base/ButtonSec.vue";
import SearchSelectList from "@/components/interface/elements/base/SearchSelectList.vue";
import NotificationModal from "@/components/interface/elements/base/NotificationModal.vue";
import SwitchSelection from "@/components/interface/elements/base/SwitchSelection.vue";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";

export default {
  name: 'StoragePipelineModal',
  components: {SwitchSelection, NotificationModal, SearchSelectList, ButtonSec, FileSelect},
  data() {
    return {
      loadMode: false,

      serverTarget: true,
      errorMessage: "",
      loadingPipeline: false,

      selectedPipeline: "",
    }
  },
  methods: {
    show (loadMode) {
      this.loadMode = loadMode;

      this.selectedPipeline = "";

      if(!this.loadMode) this.selectedPipeline = PipelineService.pipelineMetaData.getName();

      this.$modal.show('loadPipelineModal');
    },

    hide () {
      this.$modal.hide('loadPipelineModal');
    },

    // -------------- Loading --------------

    async _loadPipelineFile(content) {
      if(this.loadingPipeline) return;

      this.errorMessage = "";
      this.loadingPipeline = true;

      let loadedPipe = null;

      try {
        loadedPipe = JSON.parse(content);
      } catch {
        this.errorMessage = "Pipeline couldn't be loaded!"
        this.loadingPipeline = false;

        return;
      }

      await this._performPipelineLoad(loadedPipe);
    },

    _loadServerPipeline(pipeline) {
      if(this.loadingPipeline) return;

      this.errorMessage = "";
      this.loadingPipeline = true; // Sometimes DOM is not updated due to some weird Vue interaction with async?
      PipelineService.pipelineMetaData.updateName(pipeline);

      let ths = this;

      setTimeout(function() {
        NetworkService.requestStoredPipeline(pipeline).then(async function(loadedPipe) {
          if(loadedPipe == null || loadedPipe.length === 0) {
            ths.errorMessage = "Pipeline couldn't be loaded!"
            ths.loadingPipeline = false;

            return;
          }

          await ths._performPipelineLoad(JSON.parse(loadedPipe));
        });
      }, 100); // Give some time to update UI with loading, otherwise vue is sometimes missing the DOM updates...
    },

    async _performPipelineLoad(loadedPipe) {
      try {
        await DataExportService.loadSaveData(loadedPipe);

        this.hide();
      } catch(err) {
        console.log(err);
        this.errorMessage = "An error occurred during loading!";
      }

      this.loadingPipeline = false;
    },

    // -------------- Storing --------------

    _savePipeline() {
      this.errorMessage = "";

      this.selectedPipeline = this.selectedPipeline.trim();
      if(this.selectedPipeline.length === 0) return;

      // Check if name exists

      if(this.serverTarget && this.$refs.storageList.dataArray.includes(this.selectedPipeline)) {
        this._showConfirmationModal(
            "Override confirmation",
            "Are you sure to override<br><i>" + this.selectedPipeline + "</i>?",
            this._performPipelineSave);
      } else this._performPipelineSave();
    },

    _performPipelineSave() {
      PipelineService.pipelineMetaData.updateName(this.selectedPipeline);

      let saveData = DataExportService.createSaveData();

      if(!this.serverTarget) {
        //Export file

        let element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(saveData));
        element.setAttribute('download', this.selectedPipeline + ".json");

        element.style.display = 'none';
        document.body.appendChild(element);

        element.click();

        document.body.removeChild(element);

        this.selectedPipeline = "";

        this.hide();
      } else {
        let ths = this;
        this.loadingPipeline = true;

        NetworkService.storePipeline({"name": this.selectedPipeline, "data": saveData}).then(function (res) {
          ths.loadingPipeline = false;

          if(res) {
            ths.selectedPipeline = "";
            ths.hide();
          } else ths.errorMessage = "Couldn't store pipelineState!";
        });
      }
    },

    // -------------- Utils --------------

    _onPipelineClick(pipeline) {
      if(this.loadMode) this._loadServerPipeline(pipeline);
      else {
        this.selectedPipeline = pipeline;

        this._savePipeline();
      }
    },

    _showConfirmationModal(title, text, confirm) {
      this.$modal.show('storageConfirmModal', {title: title, content: text,
        confirmAction: confirm, cancelAction: () => this.$modal.hide('storageConfirmModal')});
    },

    _deleteServerPipeline(pipeline) {
      this._showConfirmationModal(
          "Delete confirmation",
          "Are you sure to delete<br><i>" + pipeline + "</i>?",
          () => this._confirmServerPipelineDeletion(pipeline));
    },

    _confirmServerPipelineDeletion(pipeline) {
      let ths = this;
      let storageList = this.$refs.storageList;

      NetworkService.deleteStoredPipeline(pipeline).then(function(res) {
        if(res != null) storageList.updateDataArray(storageList.dataArray.filter(v => v !== pipeline));

        ths.$modal.hide('storageConfirmModal');
      });
    },

    _selectTarget(server) {
      this.errorMessage = "";
      this.serverTarget = server;

      if(this.serverTarget) {
        let storageList = this.$refs.storageList;
        storageList.loading = true;
        storageList.errorMessage = "";

        storageList.clearSearch();

        NetworkService.listStoredPipelines().then(function(pipelines) {
          storageList.loading = false;

          if(pipelines == null) { // Server not connected
            storageList.errorMessage = "Couldn't load pipelines!";

            return;
          }

          storageList.updateDataArray(pipelines);
        });
      }
    }
  }
}
</script>

<style scoped>

.targetContent {
  margin-top: 10px;
}

.errorContainer {
  margin-top: 5px;
  color: red;
}

.loading {
  pointer-events: none;
  opacity: 0.75;
}

</style>

<style>
.pipelineSearchList .loader:after {
  background: var(--main-bg-color);
}
</style>
