<template>
  <modal ref="modal" name="SavePipelineModal" transition="pop-out" :width="200" height="auto" :shiftY="0.1" :shiftX="0.1">
    <div style="padding:10px;">
      <div><b>Enter Pipeline Name!</b></div>
      <br/>

      <input type="text" v-model="inputText" style="width: 95%;">

      <div style="display:inline-block; margin-top:10px;">
        <button style="display:inline; margin:4px;" @click="hide">Close</button>
        <button style="display:inline; margin:4px;" @click="confirm">Save</button>
      </div>
    </div>
  </modal>
</template>

<script>
import {createSaveData} from "@/scripts/tools/Utils";

export default {
  name: 'SavePipelineModal',
  methods: {
    show () {
      this.$modal.show('SavePipelineModal');
    },
    hide () {
      this.$modal.hide('SavePipelineModal');
    },
    confirm() {
      let text = this.inputText.trim();
      if(text.length === 0) return;

      //Export file

      let element = document.createElement('a');
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(createSaveData()));
      element.setAttribute('download', text + ".json");

      element.style.display = 'none';
      document.body.appendChild(element);

      element.click();

      document.body.removeChild(element);

      this.hide();
    }
  },
  data() {
    return {
      inputText: "Pipeline"
    }
  }
}
</script>
