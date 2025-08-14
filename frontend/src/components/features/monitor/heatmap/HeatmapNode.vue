<template>
  <div ref="element" class="heatmapNode" :style="'box-shadow: 0px 0px 125px 75px '
    + heatmapColor + '; transform:translate(' + posX + 'px, ' + posY + 'px);' +
     'width: ' + w + 'px; height: ' + h + 'px; z-index:' + Math.round(vueNode.heatmapRating * 100) + ';'"></div>
</template>

<script>
import {calcHeatmapColor} from "@/scripts/tools/Utils";

export default {
  name: "HeatmapNode",
  props: ["vueNode", "node"],
  data() {
    return {
      posX: 0,
      posY: 0,
      w: 0,
      h: 0
    }
  },
  methods: {
    updateNode() {
      // Do not include borders (offsetWidth) to avoid aliasing on the edges, also border of node changes
      this.w = this.vueNode.$el.clientWidth;
      this.h = this.vueNode.$el.clientHeight;

      this.posX = this.node.position[0];
      this.posY = this.node.position[1];
    }
  },
  computed: {
    heatmapColor() {return calcHeatmapColor(this.vueNode.heatmapRating)}
  },
  mounted() {
    this.resizeObserver = new ResizeObserver(this.updateNode);
    this.resizeObserver.observe(this.vueNode.$el);
  },
  beforeDestroy () {
    this.resizeObserver.unobserve(this.vueNode.$el);
  }
}
</script>

<style scoped>
.heatmapNode {
  position: absolute;
  width: 200px;
  height: 200px;
  pointer-events: none;
  touch-action: none;
  border-radius: var(--node-border-radius);
  transform-origin: center;
}
</style>
