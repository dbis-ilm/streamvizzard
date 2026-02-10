<template>
  <ResizeElement :resizeKey="param.key" :autoHide="true" :operator="param.operator" :title="param.tooltip" class="controlContainer">
    <span v-if="param.title && param.title.length > 0" class="compSettingsTitle" :title="param.title">{{ param.title }}</span>
    <input type="number" :value="param.value" :min="param.min" :max="param.max" @change="change($event)" class="compSettings editorInput"/>
  </ResizeElement>
</template>

<script>

import ResizeElement from "@/components/pipeline/operator/ResizeElement.vue";

export default {
  components: {ResizeElement},
  props: {
    /** @type NumberParam **/
    param: {required: true},
  },

  methods: {
    change(e){
      this.param.setValue(e.target.value);
      this.$forceUpdate(); // Force update in case value is clamped back to original which does not update input field
    },
  }
}
</script>

<style scoped>

input[type=number] {
  appearance: textfield;
}

</style>
