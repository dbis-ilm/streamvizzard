<template>
  <div :title="tooltip" class="controlContainer">
    <span v-if="description && description.length > 0" class="compSettingsTitle" :title="description">{{ description }}&nbsp;</span>
    <input type="text" :readonly="readonly" :value="value" @change="change($event)" @dblclick.stop="" @pointermove.stop="" class="compSettings"/>
  </div>
</template>

<script>
import {makeResizable} from "@/scripts/tools/Utils";
import $ from "jquery";

export default {
  props: ['readonly', 'emitter', 'ikey', 'getData', 'putData', 'defaultVal', 'tooltip', 'description', 'node', 'ctrl'],
  data() {
    return {
      value: ''
    }
  },
  methods: {
    change(e){
      let oldVal = this.value;

      this.value = e.target.value;

      if (this.ikey) this.putData(this.ikey, this.value);

      this.node.component.onControlValueChanged(this.ctrl, this.node, oldVal);
    }
  },
  mounted() {
    this.value = this.defaultVal;

    makeResizable($(this.$el), this.node, this.ikey,  true);
  }
}
</script>

<style scoped>

</style>
