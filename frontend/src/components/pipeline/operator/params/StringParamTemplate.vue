<template>
  <ResizeElement :resizeKey="param.key" :autoHide="true" :operator="param.operator" :title="param.tooltip" class="controlContainer">
    <span v-if="param.title && param.title.length > 0" class="compSettingsTitle" :title="param.title">{{ param.title }}&nbsp;</span>
    <input type="text" :value="param.value" @change="change($event)" class="compSettings editorInput">
  </ResizeElement>
</template>

<script>

import ResizeElement from "@/components/pipeline/operator/ResizeElement.vue";

export default {
  components: {ResizeElement},
  props: {
    /** @type StringParam **/
    param: {required: true},
  },

  methods: {
    change(e){
      this.param.setValue(e.target.value);
      this.$forceUpdate();
    }
  },
}

</script>
