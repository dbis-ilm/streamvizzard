<template>
  <vue-slider ref="slider" :value="sliderVal" v-bind="options" @change="_onValueChange"
              :tooltip-formatter="val => _getDisplayValue(val) + ' x'"
              @drag-start="_onDragStart" @drag-end="_onDragEnd"/>
</template>

<script>

export default {
  name: "HistoryRewindSpeedSlider",
  props: ["value"],

  data() {
    return {
      options: {
        dotSize: 14,
        min: -99,
        max: 100,
        interval: 1,
        tooltipPlacement: 'left'
      }
    }
  },

  computed: {
    sliderVal() {
      if(this.value < 1) return -(1 / this.value) + 1;
      else if(this.value > 1) return this.value;
      else return 0;
    }
  },

  methods: {
    _getDisplayValue(val) {
      if(val > 0) return val;
      else if(val < 0) return "1/" + Math.abs(val - 1);
      else return 1;
    },

    _getRealValue(val) {
      if(val > 0) return val;
      else if(val < 0) return (1 / Math.abs(val - 1));
      else return 1;
    },

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
      newVal = this._getRealValue(newVal);

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
