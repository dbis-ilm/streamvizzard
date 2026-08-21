<template>
  <ResizeElement :resizeKey="'DT'" :autoHide="true" :operator="operator" class="previewImg">
    <img :src="'data:image/png;base64,' + imgData" :class="'editorInput img ' + (imgData != null ? '' : 'empty')" @dblclick.stop="" :width="width" :height="height" alt=" " @pointermove.stop="" style="display:block; pointer-events: none"/>
  </ResizeElement>
</template>

<script>

import {valueOr} from "@/scripts/tools/Utils";
import ResizeElement from "@/components/pipeline/operator/ResizeElement.vue";

export default {
  components: {ResizeElement},
  inject: ['performTrackedRender'],
  props: {
    /** @type {SvOperator} **/
    operator: {required: true},
    settings: {type: Object, required: true},
    value: {required: true},
  },

  data() {
    return {
      imgData: null,
      width: 220,
      height: 220
    }
  },

  watch: {
    value() {
      this.performTrackedRender(() => { this.imgData = this.value != null ? this.value["data"] : null; });
    }
  },

  methods: {
    onResize(entries) {
      let newW = 0;
      let newH = 0;

      entries.forEach(entry => {
        newW = entry.contentRect.width;
        newH = entry.contentRect.height;
      });

      this.width = newW;
      this.height = newH;

      // Do not override other settings | Clone to trigger update
      let set = valueOr(Object.assign({}, this.operator.monitor.displayModeSettings), {});

      set.w = newW;
      set.h = newH;

      this.operator.monitor.updateDisplayModeSettings(set);
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
  text-align: center;

  height: 100%;
  width: 100%;

  min-width: 220px;
  min-height: 220px;
}

.img {
  background: var(--main-hover-color);  /* Workaround to hide jagged edges on scroll */
  border-radius: 2px;
  border: 1px solid var(--main-hover-color);
  box-sizing: border-box;
}

.img.empty {
  background: white;
}

</style>
