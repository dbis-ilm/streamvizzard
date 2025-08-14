<template>
  <div :title="tooltip" class="controlContainer" v-if="ctrl.show">
    <span v-if="description && description.length > 0" class="compSettingsTitle" :title="description">{{ description }}</span>
    <input class="editorInput" type="checkbox" :readonly="readonly" :checked="value" @change="change($event)" style="width: 30px; margin-left: 0;"/>
    <span style="flex-grow: 1"></span>
  </div>
</template>

<script>

export default {
  props: ['readonly', 'cKey', 'defaultVal', 'tooltip', 'description', 'node', 'ctrl'],
  data() {
    return {
      value: false,
    }
  },
  methods: {
    setData(data) {
      let oldVal = this.value;

      this.value = data;

      if(oldVal !== this.value) this.node.component.onControlValueChanged(this.ctrl, this.node, oldVal);
    },

    change(e){
      this.setData(e.target.checked);

      // Avoid element being selected after clicking, not intuitive for user
      e.target.blur();
    }
  },
  mounted() {
    this.value = this.defaultVal;
  }
}
</script>
