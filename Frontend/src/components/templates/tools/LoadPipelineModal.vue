<template>
  <modal ref="modal" name="loadPipelineModal" transition="pop-out" :width="200" height="auto" :shiftY="0.1" :shiftX="0.1">
    <div style="padding:10px;">
      <div><b>Select The Pipeline!</b></div>
      <br/>

      <FileSelect @input="confirm" extensions=".json"></FileSelect>

      <div style="display:inline-block; margin-top:10px;">
        <button style="display:inline; margin:4px;" @click="hide">Close</button>
      </div>
    </div>
  </modal>
</template>

<script>

import FileSelect from "@/components/templates/tools/FileSelect";
import {loadSaveData} from "@/scripts/tools/Utils";

export default {
  name: 'LoadPipelineModal',
  components: {FileSelect},
  methods: {
    show () {
      this.$modal.show('loadPipelineModal');
    },
    hide () {
      this.$modal.hide('loadPipelineModal');
    },
    async confirm(content) {
      await loadSaveData(JSON.parse(content));

      this.hide();
    }
  }
}
</script>
