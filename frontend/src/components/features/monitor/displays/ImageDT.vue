<template>
  <div ref="img" class="previewImg">
    <img :src="'data:image/png;base64,' + value" class="editorInput" @dblclick.stop="" :width="width" :height="height" alt="" @pointermove.stop="" style="display:block; pointer-events: none"/>
  </div>
</template>

<script>

import NumberDS from "@/components/features/monitor/displays/settings/NumberDS.vue";
import {safeVal} from "@/scripts/tools/Utils";

export default {
  props: ['value', 'control'],

  data() {
    return {
      width: 220,
      height: 220
    }
  },

  methods: {
    setValue(value) {
      this.value = value != null ? value["data"] : null;
    },

    onResize(entries) {
      let newW = 0;
      let newH = 0;

      entries.forEach(entry => {
        newW = entry.contentRect.width;
        newH = entry.contentRect.height;
      });

      this.width = newW;
      this.height = newH;

      //Do not override other settings
      let set = this.control.settings;
      if(set == null) return;
      set.w = newW;
      set.h = newH;

      this.control.onSettingsChanged(set);
    },

    getSettingsOptions(props, propsDef) {
      return [{"key": "mult", "name": "Multiplier", "value": props.mult, "desc": "The value to multiply with the image", "default": safeVal(propsDef.mult), "template": NumberDS}];
    },
  },
  mounted() {
    this.resizeObserver = new ResizeObserver(this.onResize);
    this.resizeObserver.observe(this.$el);
  },

  beforeDestroy() {
    this.resizeObserver.unobserve(this.$el);
  }
}
</script>

<style scoped>

.previewImg {
  background: white;
  text-align: center;

  height: 100%;
  width: 100%;

  min-width: 220px;
  min-height: 220px;
}

</style>
