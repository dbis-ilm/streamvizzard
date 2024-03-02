<template>
  <div :title="tooltip" class="clearfix controlContainer">
    <span v-if="description && description.length > 0" class="compSettingsTitle" :title="description">{{ description }}</span>
    <v-select :options="options" :readonly="readonly" label="title" :value="value" :clearable="false" :searchable="false" style="float:left;" @input="change($event)" @dblclick.stop="" @pointermove.stop="" class="compSettings"></v-select>
  </div>
</template>

<script>
import "vue-select/dist/vue-select.css";
import {makeResizable} from "@/scripts/tools/Utils";
import $ from "jquery";

export default {
  props: ['readonly', 'emitter', 'ikey', 'getData', 'putData', 'tooltip', 'description', 'options', 'defaultVal', 'node', 'ctrl'],
  data() {
    return {
      value: {title: ""}
    }
  },
  methods: {
    change(e){
      let oldValue = this.value.key;

      this.value = e;

      if (this.ikey) this.putData(this.ikey, this.value);

      this.node.component.onControlValueChanged(this.ctrl, this.node, oldValue);
    }
  },
  mounted() {
    this.value = this.options.find(el => el.key === this.defaultVal);

    makeResizable($(this.$el), this.node, this.ikey, true);
  }
}
</script>

<style>

.v-select {
  display: grid;
}

</style>
