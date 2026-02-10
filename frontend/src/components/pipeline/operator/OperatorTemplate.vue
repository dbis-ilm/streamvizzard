<template>
  <div class="opContainer" :style="'z-index: ' + this.operator.order + '; transform: translate(' + operator.posX + 'px, ' + operator.posY + 'px);'"
       @contextmenu="_onContextMenu" v-draggable="{dragStart: this._onDragStart, dragging: this._onDragging, dragEnd: this._onDragEnd}">
    <div ref="operator" :class="['node', selected && 'selected', 'mod_' + operator.definition.path[0]]"  :style="'background:' + operator.definition.bgColor">
      <div class="outlineSmooth"/>
      <div class="ctrlRow">
        <div class="titleContainer" :title="operator.name"><AutoScaleTextarea ref="nameInput" :value="operator.name" class="title editorInput editorNameInput" @change=onViewNameChange($event)></AutoScaleTextarea></div>
        <div style="right: 0; top: -2px; position:absolute;">
          <i :class="'ctrlIcon bi bi-sliders2-vertical ' + (operator.showSettings ? '' : 'activated')" title="Toggle operator settings" @click="onSettingsToggleClick()"></i>
          <i :class="'ctrlIcon bi bi-graph-up ' + (operator.showData ? '' : 'activated')" title="Toggle data display" @click="onMonitorToggleClick()"></i>
          <i class="ctrlIcon bi bi-x-circle" title="Remove Operator" @click="onRemove" @pointerdown.stop=""></i>
        </div>
        <div style="left: 0; top: -2px; position: absolute;">
          <i class="bi bi-stop-circle ctrlIcon" v-if="$streamvizzard.debugger.enabled && activeBreakpoint" :style="'visibility:visible; ' + (breakPointTriggered ? 'color:red;' : '')"
             :title="breakPointTriggered ? 'Breakpoint triggered!' : 'Has active breakpoints!'"></i>
          <i class="bi bi-question-circle ctrlIcon" v-if="$streamvizzard.advisor.enabled && operator.advisorSuggestions != null" style="visibility:visible; color: var(--warning-color);" title="Advisions are available!"></i>
          <i class="bi bi-exclamation-circle ctrlIcon" v-if="operator.errorMsg != null" style="visibility:visible; color: var(--error-color);" title="An error occurred!"></i>
          <i class="bi bi-info-circle ctrlIcon" v-if="manualCompileTarget" style="visibility:visible;" title="Operator has manual compilation target!"></i>
          <i class="bi bi-shuffle ctrlIcon" v-if="outOfOrderOccurrence" style="visibility:visible;" title="Operator processes out-of-order tuples!"></i>
        </div>
      </div>
      <div class="content">
        <div class="col"><SocketTemplate v-for="input in operator.inputs" :key="input.templateKey" :socket="input" style="text-align: left"/></div>
        <div class="col mainContent">
          <DisplayTemplate :operator="operator" v-show="operator.showData"/>
          <div class="param" v-for="param in operator.params" :key="param.key">
            <component class="control" :is="param.getTemplate()" :param="param" v-show="operator.showSettings && param.show"/>
          </div>
        </div>
        <div class="col"><SocketTemplate v-for="output in operator.outputs" :key="output.templateKey" :socket="output"/></div>
      </div>
    </div>
  </div>
</template>

<script>
import $ from 'jquery'
import {makeNameInput} from "@/scripts/tools/Utils";
import {EVENTS, executeEvent, INTERACTION} from "@/scripts/tools/EventHandler";
import AutoScaleTextarea from "@/components/interface/elements/base/AutoHeightTextarea.vue";
import DisplayTemplate from "@/components/features/monitor/displays/DisplayTemplate.vue";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";
import SocketTemplate from "@/components/pipeline/SocketTemplate.vue";
import OpStepNotification from "@/components/features/debugger/OpStepNotification.vue";

export default {
  props: {
    operator: {type: SvOperator, required: true},
  },

  components: {
    OpDebugStepOverlay: OpStepNotification,
    SocketTemplate,
    DisplayTemplate,
    AutoScaleTextarea},

  data() {
    return {
      dragAnchor: null,
    }
  },

  provide() {
    return {
      operatorView: this
    };
  },

  methods: {
    onSettingsToggleClick: function() {
      this.operator.showSettings = !this.operator.showSettings;
    },

    onMonitorToggleClick: function() {
      this.operator.showData = !this.operator.showData;
    },

    onRemove: function(e) {
      e.stopPropagation();

      this.$streamvizzard.pipeline.deleteOperator(this.operator);
    },

    onViewNameChange: function(event) {
      let prevValue = this.operator.name;

      this.operator.name = event.target.value.trim();
      if(this.operator.name.length === 0) this.operator.name = this.operator.definition.displayName;

      executeEvent(EVENTS.OP_NAME_CHANGED, [this.operator, prevValue]);
    },

    // ----------------------------------------------------- Events ----------------------------------------------------

    _onContextMenu(e) {
      e.preventDefault();
      e.stopPropagation();

      this.$streamvizzard.editor.openOperatorContextMenu(e.clientX, e.clientY, this.operator);
    },

    _onDragStart() {
      this.$streamvizzard.editor.selectOperator(this.operator);

      this.dragAnchor = {
        x: this.operator.posX - this.$streamvizzard.editor.mouseX,
        y: this.operator.posY - this.$streamvizzard.editor.mouseY
      };

      executeEvent(EVENTS.OP_INTERACTED, [this.operator, INTERACTION.DRAG_START]);
    }
,
    _onDragging() {
      this.operator.moveTo(this.$streamvizzard.editor.mouseX + this.dragAnchor.x,
          this.$streamvizzard.editor.mouseY + this.dragAnchor.y);

      // Moving the operator requires the DOM to update before elm and children boundingClientRect (sockets) are up to date
      // -> Defer the snapping and event handling until components are updated (still in same frame)

      this.$nextTick(() => {
        // Need to rely on drag anchor to escape snapping
        let snappedPos = this.$streamvizzard.editor.calculateOperatorSnapping(this.operator);
        if (snappedPos != null) this.operator.moveTo(snappedPos.x, snappedPos.y);

        executeEvent(EVENTS.OP_INTERACTED, [this.operator, INTERACTION.DRAGGING]);
      });
    },

    _onDragEnd() {
      this.dragAnchor = null;

      this.$streamvizzard.editor.clearSnappingLines();

      executeEvent(EVENTS.OP_INTERACTED, [this.operator, INTERACTION.DRAG_END]);
    }
  },

  computed: {
    selected() {
      return this.$streamvizzard.editor.selectedOperator === this.operator;
    },

    activeBreakpoint() {
      for(let p of this.operator.breakPoints) {
        if (p.enabled) return true;
      }

      return false;
    },

    breakPointTriggered() {
      for(let p of this.operator.breakPoints) {
        if (p.triggered) return true;
      }

      return false;
    },

    manualCompileTarget() {
      return this.$streamvizzard.compiler.isActive() && this.operator.compiler.config?.manual;
    },

    outOfOrderOccurrence() {
      return this.$streamvizzard.compiler.isActive() && this.operator.compiler.specs?.metaData.outOfOrderProcessing;
    }
  },

  mounted() {
    makeNameInput($(this.$refs.nameInput.$el), $(this.$refs.nameInput.$el).closest("div"));

    this.resizeObserver = new ResizeObserver(() => {
      this.operator.width = this.$refs.operator.clientWidth;
      this.operator.height = this.$refs.operator.clientHeight;

      executeEvent(EVENTS.OP_SIZE_CHANGED, this.operator);
    });

    this.operator.width = this.$refs.operator.clientWidth;
    this.operator.height = this.$refs.operator.clientHeight;

    this.resizeObserver.observe(this.$refs.operator);
  },

  beforeDestroy () {
    this.resizeObserver.unobserve(this.$refs.operator);
  }
}

</script>

<style scoped>

.node {
  border-radius: var(--node-border-radius);
  cursor: pointer;
  min-width: 180px;
  min-height: 180px;
  box-sizing: border-box;
  position: relative;
  user-select: none;

  box-shadow: 0 0 0 calc(2px * var(--editor-scale-fac)) var(--node-outline-color);
}

.node.selected {
  box-shadow: 0 0 0 calc(4px * var(--editor-scale-fac)) var(--main-font-color);
}

.node .outlineSmooth {
  /* Fills the node background with the border color to hide pixelation issues at the edges */
  width: calc(100% + 2px);
  height: calc(100% + 2px);
  position: absolute;
  border-radius: inherit;
  top: -1px;
  left: -1px;
  background: var(--node-outline-color);
  z-index: -1;
}

.node .content {
  width: 100%;
  height: calc(100% - 56px); /* 40 + padding */
  padding-bottom: 10px;
  display:flex;
  flex-direction: column;
}

.node .mainContent {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  margin-left: 10px;
  margin-right: 10px;
  height: 100%;
}

.node .param {
  margin: 4px 0;
}

.node .title {
  width: 100%;
  font-size: var(--node-title-font-size);
  padding: 0;
  text-align:center;

  resize: none;
}

.node .titleContainer {
  padding-top: 20px;
}

.node .ctrlRow {
  height: unset;
  top: unset;

  padding: 5px 10px 10px;
}

</style>
