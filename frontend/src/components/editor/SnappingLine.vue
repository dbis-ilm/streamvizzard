<template>
  <div :class="'snappingLine ' + (line.horizontal ? 'horizontal' : 'vertical')" :style="'transform: ' + transform"/>
</template>

<script>

import SnappingLine from "@/scripts/editor/SnappingLine";

export default {
  props: {
    line: {type: SnappingLine, required: true},
  },

  computed: {
    transform() {
      let scale = this.line.horizontal ? "scale(100000, var(--editor-scale-fac))" : "scale(var(--editor-scale-fac), 100000)"

      return "translate(" + (this.line.posX) + "px, " + (this.line.posY) + "px) translate(-50%, -50%) " + scale;
    }
  }
}

</script>

<style scoped>

.snappingLine {
  opacity: 0.25;
  pointer-events: none;

  background: var(--main-hover-color);
}

.snappingLine.horizontal {
  width: 100vw;
  height: 2px;
}

.snappingLine.vertical {
  height: 100vh;
  width: 2px;
}

</style>
