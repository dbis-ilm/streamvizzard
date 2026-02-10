<template>
  <ResizeElement :resizeKey="param.key" :autoHide="true" :operator="param.operator" :title="param.tooltip" class="clearfix controlContainer">
    <span v-if="param.title && param.title.length > 0" class="compSettingsTitle" :title="param.title">{{ param.title }}</span>
    <v-select v-auto-blur ref="select" :options="param.options" label="title" :value="selected" :clearable="false" :searchable="false"
              style="float:left;" @open="openedDropdown" @close="closedDropdown" @input="change($event)" class="compSettings editorInput"></v-select>
  </ResizeElement>
</template>

<script>
import "vue-select/dist/vue-select.css";
import {Services} from "@/scripts/services/Services";
import ResizeElement from "@/components/pipeline/operator/ResizeElement.vue";

export default {
  components: {ResizeElement},
  props: {
    /** @type SelectParam **/
    param: {required: true},
  },

  computed: {
    selected() {
      return this.param.options.find(option => option.key === this.param.value);
    }
  },

  methods: {
    change(e){
      this.param.setValue(e.key);
    },

    openedDropdown() {
      Services.EditorInputManager.onInputSelected(this.$refs.select.$el);
    },

    closedDropdown() {
      Services.EditorInputManager.onInputDeselected(this.$refs.select.$el);
    }
  },

  mounted() {
    this.$refs.select.$el.addEventListener("deactivate", () => {
      this.$refs.select.$el.querySelector("input").blur();
    });

    this.$refs.select.$el.addEventListener("activate", () => {
      this.$refs.select.$el.querySelector("input").focus();
    });
  }
}

</script>

<style>

.editorInput.v-select .vs__dropdown-toggle {
  box-shadow: 0 0 0 calc(1px * var(--editor-scale-fac)) var(--second-border-color);
  border: none !important;
  border-radius: var(--button-border-radius);
}

.editorInput[ei-active].v-select .vs__dropdown-toggle, .editorInput[ei-active].v-select .vs__dropdown-menu {
  background: var(--input-active-color);
  color: var(--main-font-color) !important;
  border: none !important;

  box-shadow: 0 0 0 calc(2px * var(--editor-scale-fac)) var(--main-font-color);
}

.editorInput[ei-active].v-select .vs__dropdown-menu {
  margin-top: -2px;
}

</style>
