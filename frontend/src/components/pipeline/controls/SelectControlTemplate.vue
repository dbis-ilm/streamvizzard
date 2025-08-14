<template>
  <div :title="tooltip" class="clearfix controlContainer" v-if="ctrl.show">
    <span v-if="description && description.length > 0" class="compSettingsTitle" :title="description">{{ description }}</span>
    <v-select v-auto-blur ref="select" :options="options" :readonly="readonly" label="title" :value="value" :clearable="false" :searchable="false"
              style="float:left;" @open="openedDropdown" @close="closedDropdown" @input="change($event)" class="compSettings"></v-select>
  </div>
</template>

<script>
import "vue-select/dist/vue-select.css";
import {makeResizable} from "@/scripts/tools/Utils";
import $ from "jquery";
import {EditorInputManager} from "@/scripts/services/EditorInputManager";

export default {
  props: ['readonly', 'cKey', 'tooltip', 'description', 'options', 'defaultVal', 'node', 'ctrl'],
  data() {
    return {
      value: {title: ""}
    }
  },
  methods: {
    setData(data) {
      let oldValue = this.value.key;

      this.value = data;

      if(oldValue !== this.value) this.node.component.onControlValueChanged(this.ctrl, this.node, oldValue);
    },

    change(e){
      this.setData(e);
    },

    openedDropdown() {
      EditorInputManager.onInputSelected(this.$refs.select.$el);
    },

    closedDropdown() {
      EditorInputManager.onInputDeselected(this.$refs.select.$el);
    }
  },
  mounted() {
    this.value = this.options.find(el => el.key === this.defaultVal);

    makeResizable($(this.$el), this.node, this.cKey, true);
  }
}
</script>

<style>

.v-select {
  display: grid;
}

</style>
