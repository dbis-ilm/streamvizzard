<template>
  <div :class="['reroutePin', pin.con.highlighted && 'conSelected']"
       :style="'transform: translate(' + this.pin.x + 'px, ' + this.pin.y + 'px) translate(-50%, -50%); ' +
        'z-index: ' + (pin.con.order != null ? pin.con.order : '')"
       :title="'Drag and move to reroute the connection!' + '\n' + 'Click to remove the rerouting point!'"
       draggable="false" v-draggable="{dragStart: this._onDragStart, dragging: this._onDragging, dragEnd: this._onDragEnd}"
       @mouseover="_onHover(true)" @mouseout="_onHover(false)" @mouseup="_onDelete">
  </div>
</template>

<script>

import {ReroutePin} from "@/scripts/pipeline/SvConnection";

export default {
  name: "ReroutePin",
  props: {
    pin: {type: ReroutePin, required: true},
  },

  data() {
    return {
      moved: false,
    }
  },

  methods: {
    _onDragStart() {
      this.moved = false;
    },

    _onDragging() {
      this.moved = true;

      this.pin.con.updateReroutePin(this.pin, this.$streamvizzard.editor.mouseX, this.$streamvizzard.editor.mouseY);

      let snappedPos = this.$streamvizzard.editor.calculatePinSnapping(this.pin);
      if(snappedPos != null) this.pin.con.updateReroutePin(this.pin, snappedPos.x, snappedPos.y);
    },

    _onDragEnd() {
      this.$streamvizzard.editor.clearSnappingLines();
    },

    _onDelete(e) {
      if(this.moved || e.button !== 0) return;

      this.pin.con.removeReroutePin(this.pin);
    },

    _onHover(hovered) {
      this.pin.con.highlighted = hovered;
    },
  },
}

</script>

<style scoped>

  .reroutePin {
    border-radius: 50%;
    cursor: pointer;
    pointer-events: all;
    user-select: none;

    width: 7px;
    height: 7px;
    background: white;
    border: 4px solid var(--connection-color);
  }

  .reroutePin.conSelected {
    box-sizing: border-box;
    border-color: var(--main-hover-color);
    width: 20px;
    height: 20px;
  }

  .reroutePin.conSelected:hover {
    background: var(--connection-color);
  }

</style>

