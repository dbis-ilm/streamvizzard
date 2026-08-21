<template>
  <div :class="['connection', connection.highlighted && 'selected', focused && 'focused']" @mouseover="_onMouseOver" @mouseout="_onMouseOut"
       @contextmenu="_onContextMenu" :style="connection.order != null ? 'z-index: ' + connection.order : ''">
    <svg>
      <path class="visualPath" :d="pathData" :style="'stroke-dashoffset: ' + connection.strokeDashOffset"></path>
      <path class="interactPath" :d="pathData" @click="_onPathClick">
        <title class='conHoverTitle' v-html="hoverTitle"></title>
      </path>
    </svg>
  </div>
</template>

<script>

import SvConnection from "@/scripts/pipeline/SvConnection";
import {EVENTS, registerEvent, unregisterEvent} from "@/scripts/tools/EventHandler";

export default {
  name: "ConnectionTemplate",
  props: {connection: {type: SvConnection, required: true}},

  data() {
    return {
      pathData: ""
    }
  },

  computed: {
    hoverTitle() {
      return "Connection ID: " + this.connection.id + "\nThroughput: "
      + this.connection.monitor.executionStats.currentThroughput.toFixed(2)
      + " tuples / s\nTotal tuples: " + this.connection.monitor.executionStats.totalTuples + "\n"
      + "(Click to add rerouting points!)";
    },

    focused() {
      // Focus connection if any of its reroutes is currently focused
      for(let p of this.connection.reroutes) {
        if(this.$streamvizzard.editor.focusedObjects.has(p)) return true;
      }

      return false;
    }
  },

  watch: {
    "connection.reroutes": {
      handler () {
        this.updatePathData();
      }, deep: true,
    }
  },

  methods: {
    updatePathData() {
      const [x1, y1, x2, y2] = this.connection.getEndpoints();

      if(this.connection.reroutes.length === 0) { // Default (curved)
        let curvature = 0.4;

        const hx1 = x1 + Math.abs(x2 - x1) * curvature;
        const hx2 = x2 - Math.abs(x2 - x1) * curvature;

        this.pathData = `M ${x1} ${y1} C ${hx1} ${y1} ${hx2} ${y2} ${x2} ${y2}`;
      } else { // Rerouted
        const reroutePins = this.connection.reroutes;

        const newPoints = [[x1, y1], ...reroutePins.map((pin) => [pin.x, pin.y]), [x2, y2]];

        let pd = "M";

        for(let idx in newPoints) {
          let p = newPoints[idx];

          if(idx >= 1) pd += "L ";

          pd += p[0] + "," + p[1];
        }

        this.pathData = pd;
      }
    },

    _onPathClick() {
      this.connection.addReroutePin(this.$streamvizzard.editor.mouseX, this.$streamvizzard.editor.mouseY);
    },

    /** @param {SvOperator} operator **/
    _onOpTransformUpdated(operator) {
      if(operator === this.connection.input.operator || operator === this.connection.output.operator)
        this.$nextTick(this.updatePathData); // Op needs some time to update socket DOMRects after transformation
    },

    _onContextMenu(e) {
      e.preventDefault();
      e.stopPropagation();

      this.$streamvizzard.editor.openConnectionContextMenu(e.clientX, e.clientY, this.connection);
    },

    _onMouseOver() {
      this.connection.highlighted = true;
    },

    _onMouseOut() {
      this.connection.highlighted = false;
    }
  },

  mounted() {
    this.updatePathData();

    registerEvent([EVENTS.OP_MOVED, EVENTS.OP_SIZE_CHANGED], this._onOpTransformUpdated);
  },

  beforeDestroy() {
    unregisterEvent([EVENTS.OP_MOVED, EVENTS.OP_SIZE_CHANGED], this._onOpTransformUpdated);
  }
}

</script>

<style scoped>

.connection {
  pointer-events: none;
}

svg {
  overflow: visible !important;
}

.connection path {
  stroke-linecap: round;
  stroke-dasharray: 32px, 32px;
  stroke-width: 5;
  fill: none;
  stroke: var(--connection-color);
}

.connection path.interactPath {
  pointer-events: stroke;
  stroke: transparent;
  stroke-width: 15;
  cursor: pointer;
  fill: none;
  stroke-dasharray: none;
}

.connection.selected path.visualPath {
  stroke: var(--main-hover-color);
}

.connection.focused path.visualPath {
  stroke: var(--main-font-color);
}

</style>
