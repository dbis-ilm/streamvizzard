<template>
  <div :title="tooltip" class="controlContainer">
    <span v-if="description && description.length > 0" class="compSettingsTitle" :title="description">{{ description }}</span>
    <input type="checkbox" :readonly="readonly" :checked="value" @change="change($event)" @dblclick.stop="" @pointermove.stop="" style="width: 30px; margin-left: 0;"/>
    <span style="flex-grow: 1"></span>
  </div>
</template>

<script>
export default {
  props: ['readonly', 'emitter', 'ikey', 'getData', 'putData', 'defaultVal', 'tooltip', 'description', 'node', 'ctrl'],
  data() {
    return {
      value: false,
    }
  },
  methods: {
    change(e){
      let oldVal = this.value;

      this.value = e.target.checked;

      if (this.ikey) this.putData(this.ikey, this.value);

      this.node.component.onControlValueChanged(this.ctrl, this.node, oldVal);
    }
  },
  mounted() {
    this.value = this.defaultVal;
  }
}
</script>

<style scoped>

</style>
