<template>
  <vue-slider ref="slider" :value="sliderVal" v-bind="options" @change="_onValueChange"
              :tooltip-formatter="val => val <= maxValue ? formatDataSize(val) : 'Infinite'"
              @drag-start="_onDragStart" @drag-end="_onDragEnd"/>
</template>

<script>
import {clamp, formatDataSize} from "@/scripts/tools/Utils";

export default {
  name: "HistoryMemorySlider",
  props: ["minValue", "maxValue", "value"],

  data() {
    return {
      options: {
        dotSize: 14,
        min: parseInt(this.minValue),
        max: parseInt(this.maxValue) + 1,
        interval: 1,
        tooltipPlacement: 'left'
      },

      dragging: false,
    }
  },

  computed: {
    sliderVal() {  // null signals infinite value
      if(this.value == null) return this.options.max;
      else return clamp(parseInt(this.value), this.options.min, this.options.max);
    }
  },

  methods: {
    formatDataSize,

    _resetMouseUp() {
      // Manually trigger mouseup on slider
      const e = new MouseEvent('mouseup', {
        view: window,
        bubbles: true,
        cancelable: true
      });

      this.$refs.slider.dragEnd(e);
      this.$refs.slider.blur();
    },

    _onDragStart() {
      this.dragging = true;
    },

    _onDragEnd() {
      this.dragging = false;
    },

    _handleGlobalMouseUp() {
      if(this.dragging) this._resetMouseUp();
    },

    _onValueChange(newVal) {
      newVal = clamp(parseInt(newVal), this.options.min, this.options.max);

      if(newVal > this.maxValue) newVal = null;

      this.$emit("input", newVal);
      this.$emit('change', newVal);
    }
  },

  mounted() {
    // Global listener to catch mouseup events that might be blocked by menu
    document.addEventListener("mouseup", this._handleGlobalMouseUp, true);
  }
}
</script>

<style scoped>

</style>
