<template>
  <div :title="tooltip" class="controlContainer" v-if="ctrl.show">
    <span v-if="description && description.length > 0" class="compSettingsTitle" :title="description">{{ description }}</span>
    <input type="number" :readonly="readonly" :value="value" :min="min" :max="max" @change="change($event)" class="compSettings editorInput"/>
  </div>
</template>

<script>
import {makeResizable} from "@/scripts/tools/Utils";
import $ from "jquery";

export default {
  props: ['readonly', 'cKey', 'defaultVal', 'tooltip', 'description', 'node', 'min', 'max', 'ctrl'],
  data() {
    return {
      value: 0
    }
  },
  methods: {
    setData(data) {
      let oldVal = this.value;

      this.value = data;

      if(this.max != null) this.value = Math.min(this.max, this.value);
      if(this.min != null) this.value = Math.max(this.min, this.value);

      if(oldVal !== this.value) this.node.component.onControlValueChanged(this.ctrl, this.node, oldVal);
    },

    change(e){
      this.setData(e.target.value);
    },
  },
  mounted() {
    this.value = this.defaultVal;

    makeResizable($(this.$el), this.node, this.cKey, true);
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
