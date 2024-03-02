<template>
  <vue-slider v-model="value" v-bind="options" @change="$emit('change');" :tooltip-formatter="val => _getDisplayValue(val) + ' x'"/>
</template>

<script>
export default {
  name: "HistoryRewindSpeedSlider",

  data() {
    return {
      value: 1,
      options: {
        dotSize: 14,
        min: -99,
        max: 100,
        interval: 1,
        tooltipPlacement: 'left'
      }
    }
  },

  methods: {
    getValue() {
      return this._getRealValue(this.value);
    },

    setValue(val) {
      if(val < 1) this.value = -(1 / val) + 1;
      else if(val > 1) this.value = val;
      else this.value = 0;
    },

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
