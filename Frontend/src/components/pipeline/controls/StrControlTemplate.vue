<template>
  <div :title="tooltip" class="controlContainer" v-if="ctrl.show">
    <span v-if="description && description.length > 0" class="compSettingsTitle" :title="description">{{ description }}&nbsp;</span>
    <input type="text" :readonly="readonly" :value="value" @change="change($event)" class="compSettings editorInput"/>
  </div>
</template>

<script>
import {makeResizable} from "@/scripts/tools/Utils";
import $ from "jquery";

export default {
  props: ['readonly', 'cKey', 'defaultVal', 'tooltip', 'description', 'node', 'ctrl'],
  data() {
    return {
      value: ''
    }
  },
  methods: {
    setData(data) {
      let oldVal = this.value;

      this.value = data;

      if(oldVal !== this.value) this.node.component.onControlValueChanged(this.ctrl, this.node, oldVal);
    },

    change(e){
      this.setData(e.target.value);
    }
  },
  mounted() {
    this.value = this.defaultVal;

    makeResizable($(this.$el), this.node, this.cKey,  true);
  }
}
</script>
