<template>
  <vue-slider v-model="value" v-bind="options" @change="$emit('change');" :tooltip-formatter="val => val <= maxValue ? formatDataSize(val) : 'Infinite'"/>
</template>

<script>
import {formatDataSize} from "@/scripts/tools/Utils";

export default {
  name: "HistoryMemorySlider",
  props: ["minValue", "maxValue"],

  data() {
    return {
      value: parseInt(this.maxValue),
      options: {
        dotSize: 14,
        min: parseInt(this.minValue),
        max: parseInt(this.maxValue) + 1,
        interval: 1,
        tooltipPlacement: 'left'
      }
    }
  },

  methods: {
    formatDataSize,
    getMemoryLimit() {
      return this.value <= this.maxValue ? this.value : null;
    },

    setMemoryLimit(limit) {
      if(limit == null) this.value = this.options.max;
      else this.value = Math.max(this.options.min, Math.min(this.options.max, limit));
    },

    resetMouseUp() {
      //Dummy function to force buggy mouseup event which is blocked from menu
      const e = new MouseEvent('mouseup', {
        view: window,
        bubbles: true,
        cancelable: false
      });

      document.dispatchEvent(e);
    }
  }
}
</script>

<style scoped>

</style>
