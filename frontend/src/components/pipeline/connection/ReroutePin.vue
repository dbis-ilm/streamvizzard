<template>
  <div :class="['reroutePin', pin.con.highlighted && 'conSelected', focused && 'focused']"
       :style="'transform: translate(' + this.pin.x + 'px, ' + this.pin.y + 'px) translate(-50%, -50%); ' +
        'z-index: ' + (pin.con.order != null ? pin.con.order : '')"
       :title="'Drag and move to reroute the connection!' + '\n' + 'Click to remove the rerouting point!'"
       draggable="false" v-draggable="{dragStart: this._onDragStart, dragging: this._onDragging, dragEnd: this._onDragEnd}"
       @mouseover="_onHover(true)" @mouseout="_onHover(false)" @mouseup="_onDelete" @contextmenu="_onContextMenu">
  </div>
</template>

<script>

import {ReroutePin} from "@/scripts/pipeline/SvConnection";
import {EVENTS, executeEvent, INTERACTION} from "@/scripts/tools/EventHandler";

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

  computed: {
    focused() {
      return this.$streamvizzard.editor.focusedObjects.has(this.pin);
    }
  },

  methods: {
    _onDragStart() {
      this.$streamvizzard.editor.selectEditorObject(this.pin);

      this.moved = false;

      executeEvent(EVENTS.CONNECTION_REROUTES_INTERACTED, [this.pin, INTERACTION.DRAG_START]);
    },

    _onDragging() {
      this.moved = true;

      this.$streamvizzard.editor.dragEditorObject(this.pin, this.$streamvizzard.editor.mouseX, this.$streamvizzard.editor.mouseY);

      // -> Defer in case we also move ops which need DOM update

      this.$nextTick(() => {
        let snappedPos = this.$streamvizzard.editor.calculateSelectionSnapping(this.pin.x, this.pin.y);
        if (snappedPos != null) this.$streamvizzard.editor.dragEditorObject(this.pin, snappedPos.x, snappedPos.y);

        executeEvent(EVENTS.CONNECTION_REROUTES_INTERACTED, [this.pin, INTERACTION.DRAGGING]);
      })
    },

    _onDragEnd() {
      this.$streamvizzard.editor.clearSnappingLines();

      executeEvent(EVENTS.CONNECTION_REROUTES_INTERACTED, [this.pin, INTERACTION.DRAG_END]);
    },

    _onDelete(e) {
      if(this.moved || e.button !== 0) return;

      this.pin.con.removeReroutePin(this.pin);
    },

    _onContextMenu(e) {
      e.preventDefault();
      e.stopPropagation();

      this.$streamvizzard.editor.openConnectionContextMenu(e.clientX, e.clientY, this.pin.con);
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

  .reroutePin.focused {
    border-color: var(--main-font-color);
  }

</style>

