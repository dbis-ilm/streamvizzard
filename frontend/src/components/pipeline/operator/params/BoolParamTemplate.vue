<template>
  <div :title="param.tooltip" class="controlContainer">
    <span v-if="param.title && param.title.length > 0" class="compSettingsTitle" :title="param.title">{{ param.title }}</span>
    <input class="editorInput checkbox" type="checkbox" :checked="param.value" @change="change($event)"/>
    <span style="flex-grow: 1"></span>
  </div>
</template>

<script>

export default {
  props: {
    /** @type CodeParam **/
    param: {required: true},
  },

  methods: {
    change(e){
      this.param.setValue(e.target.checked)

      // Avoid element being selected after clicking, not intuitive for user
      e.target.blur();
    }
  }
}
</script>

<style scoped>

.checkbox {
  width: 30px;
  height: 30px;
  margin-top: 2px;
}

</style>
