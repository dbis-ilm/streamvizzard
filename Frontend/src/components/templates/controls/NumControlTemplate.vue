<template>
  <div :title="tooltip" class="controlContainer">
    <span v-if="description && description.length > 0" class="compSettingsTitle" :title="description">{{ description }}</span>
    <input type="number" :readonly="readonly" :value="value" :min="min" :max="max" @change="change($event)" @dblclick.stop="" @pointermove.stop="" class="compSettings"/>
  </div>
</template>

<script>
import {makeResizable} from "@/scripts/tools/Utils";
import $ from "jquery";

export default {
  props: ['readonly', 'emitter', 'ikey', 'getData', 'putData', 'defaultVal', 'tooltip',
    'description', 'node', 'min', 'max', 'ctrl'],
  data() {
    return {
      value: 0
    }
  },
  methods: {
    change(e){
      let oldVal = this.value;

      this.value = e.target.value;

      if(this.max != null) this.value = Math.min(this.max, this.value);
      if(this.min != null) this.value = Math.max(this.min, this.value);

      if (this.ikey) this.putData(this.ikey, this.value);

      this.node.component.onControlValueChanged(this.ctrl, this.node, oldVal);
    }
  },
  mounted() {
    this.value = this.defaultVal;

    makeResizable($(this.$el), this.node, this.ikey, true);
  }
}
</script>

<style scoped>
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox */
input[type=number] {
  -moz-appearance: textfield;
}
</style>
