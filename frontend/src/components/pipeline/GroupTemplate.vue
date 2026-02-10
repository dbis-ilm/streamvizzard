<template>
<div v-draggable="{dragStart: this._onDragStart, dragging: this._onDragging, dragEnd: this._onDragEnd}"
     :class="['nodeGroup', $streamvizzard.monitor.isHeatmapActive() && 'heatmapActive', group.nodeAddHover && 'nodeAddHover']"
     :style="'transform: translate(' + group.x + 'px, ' + group.y + 'px); width: ' + group.width + 'px; height: '
     + group.height + 'px;' + (group.order != null ? ' z-index:' + group.order : '')">
  <div class="group">
    <div class="ctrlRow">
      <div style="height: 100%; padding-top: 1px;"><input ref="nameInput" type="text" :value="group.title" @change="_onNameChange($event)" class="nameInput editorInput limitedText editorNameInput"></div>
      <div style="right: 2px; top: 0; position: absolute;"><i class="ctrlIcon bi bi-x-circle" title="Remove Group" @click="_onRemove()"></i></div>
    </div>
  </div>

</div>
</template>

<script>

import $ from 'jquery';
import {makeNameInput} from "@/scripts/tools/Utils";
import {EVENTS, executeEvent, INTERACTION} from "@/scripts/tools/EventHandler";
import {Group} from "@/scripts/pipeline/Group";

export default {
  name: "GroupTemplate",
  props: {
    group: {type: Group, required: true}
  },

  data() {
    return {
      dragAnchor: null,
    }
  },

  methods: {
    _onRemove() {
      this.group.remove();
    },

    _onNameChange(event) {
      let prev = this.group.title;

      this.group.title = event.target.value;

      executeEvent(EVENTS.GROUP_NAME_CHANGED, [this.group, prev]);
    },

    // ---------------------------------------------------- Dragging ---------------------------------------------------

    _onDragStart() {
      this.$streamvizzard.editor.selectOperator(null);

      this.group.selectGroup();

      this.dragAnchor = {
        x: this.group.x - this.$streamvizzard.editor.mouseX,
        y: this.group.y - this.$streamvizzard.editor.mouseY
      };

      this.group.cache.update();

      executeEvent(EVENTS.GROUP_INTERACTED, [this.group, INTERACTION.DRAG_START]);
    },

    _onDragging() {
      this.group.moveGroup(this.$streamvizzard.editor.mouseX + this.dragAnchor.x,
          this.$streamvizzard.editor.mouseY + this.dragAnchor.y);

      // Defer the snapping until component DOMs are updated (still in same frame) after group/op movement

      this.$nextTick(() => {
        // Need to rely on drag anchor to escape snapping
        let snappedPos = this.$streamvizzard.editor.calculateGroupSnapping(this.group);
        if(snappedPos != null) this.group.moveGroup(snappedPos.x, snappedPos.y);
      })
    },

    _onDragEnd() {
      this.group.unselectGroup();

      this.dragAnchor = null;

      this.group.cache.clear();

      this.$streamvizzard.editor.clearSnappingLines();

      executeEvent(EVENTS.GROUP_INTERACTED, [this.group, INTERACTION.DRAG_END]);
    }
  },

  mounted() {
    makeNameInput($(this.$refs.nameInput), $(this.$refs.nameInput).closest("div"));
  },
}
</script>

<style scoped>

.group {
  width: 100%;
  height: 100%;

  position: relative;
  background: color-mix(in srgb, var(--second-bg-color), transparent 40%);
  border-radius: var(--node-border-radius);
  cursor: pointer;

  top: -6px;

  box-shadow: 0 0 0 calc(2px * var(--editor-scale-fac)) color-mix(in srgb, var(--node-outline-color), transparent 60%);
}

.heatmapActive .group {
  background: color-mix(in srgb, var(--second-bg-color), transparent 80%);
  box-shadow: 0 0 0 calc(2px * var(--editor-scale-fac)) color-mix(in srgb, var(--node-outline-color), transparent 80%);
}

.nodeAddHover .group {
  box-shadow: 0 0 0 calc(4px * var(--editor-scale-fac)) var(--main-font-color);
}

.ctrlRow {
  top: 0;
  left: 0;
  padding-top: 4px;
}

.nameInput {
  color: var(--main-hover-color);
  font-weight: bold;
  font-style: italic;

  text-align: left;
  left: 10px;
  position: absolute;
  font-size: var(--node-title-font-size);
  height: 1.25em;

  width:calc(100% - 50px);
}

</style>
