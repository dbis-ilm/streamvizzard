<template>
  <div id="editor">
    <div id="viewContainer" ref="viewContainer" @pointermove.capture="_onPointerMove" @wheel="_onScroll" @contextmenu="_onContextMenu"
         @pointerover="_onPointerOver" @pointerout="_onPointerOut" v-draggable.left.wheel="{dragStart: this._onDragStart, dragging: this._onDrag, dragEnd: this._onDragEnd}">
      <div id="view" ref="view" :style="'transform: translate(' + editor.shiftX + 'px, ' + editor.shiftY + 'px) scale(' + editor.scale + ')'">
          <div class="editorContainer heatmaps" style="z-index: 0;">
            <HeatmapOp v-show="$streamvizzard.monitor.heatmap.isActive()" v-for="op in $streamvizzard.pipeline.operators"
                       :key="'hm_' + op.templateKey" :operator="op" class="editorElm"/>
          </div>

          <div class="editorContainer pipeline" style="z-index: 1;">
            <GroupTemplate :group="group" v-for="group in $streamvizzard.pipeline.groups" :key="group.templateKey" class="editorElm editorGroup"></GroupTemplate>

            <SnappingLine :line="line" v-for="line in $streamvizzard.editor.snappingLines" :key="line.templateKey" class="editorElm editorSnappingLine"/>

            <ConnectionTemplate :connection="con" v-for="con in $streamvizzard.pipeline.connections" :key="con.templateKey" class="editorElm editorCon"/>

            <PickedConTemplate v-if="$streamvizzard.editor.pickedConnection" :connection="$streamvizzard.editor.pickedConnection" class="editorElm editorCon"/>

            <div class="reroutes">
              <div v-for="con in $streamvizzard.pipeline.connections" :key="con.id">
                <ReroutePin v-for="(pin, index) in con.reroutes" :pin="pin" :key="index" class="editorElm editorCon"/>
              </div>
            </div>

            <OperatorTemplate :operator="op" v-for="op in $streamvizzard.pipeline.operators" :key="op.templateKey" class="editorElm editorOp"></OperatorTemplate>
          </div>

          <div class="editorContainer overlay" style="z-index: 2;">
            <EditorNotification v-for="not in $streamvizzard.editor.notifications" :key="not.templateKey" :notification="not" class="editorElm"/>

            <OpStepNotification v-show="$streamvizzard.debugger.enabled" v-for="op in $streamvizzard.pipeline.operators.filter((o) => o.debugStepNotification != null)"
                           :key="op.id" :stepEx="op.debugStepNotification" :operator="op" class="editorElm"/>
          </div>
      </div>
    </div>

    <Heatmap v-if="$streamvizzard.monitor.heatmap.isActive()"/>

    <div class="selectBox" v-if="selectBox != null"
         :style="'left: ' + (selectBox.x - selectBox.offsetX) + 'px; top: ' + (selectBox.y - selectBox.offsetY) + 'px;' +
                 'width: ' + selectBox.width + 'px; height: ' + selectBox.height + 'px;'"></div>

    <div class="controlInfo noSelect" :style="'left:' + ($streamvizzard.interface.opPresetBarViewRect.right + 4) + 'px'">
      <i class="bi bi-mouse2"></i>&nbsp;Left: Select, Wheel: Move, Right: Menu, Scroll: Zoom
    </div>

    <component v-if="editor.contextMenu" :is="contextMenuTemplate" :menu="editor.contextMenu" :key="editor.contextMenu.id" :delay="50"/>
  </div>
</template>

<script>

import Heatmap from "@/components/features/monitor/heatmap/Heatmap.vue";
import {Services} from "@/scripts/services/Services";
import HeatmapOp from "@/components/features/monitor/heatmap/HeatmapOp.vue";
import GroupTemplate from "@/components/pipeline/GroupTemplate.vue";
import OperatorTemplate from "@/components/pipeline/operator/OperatorTemplate.vue";
import ConnectionTemplate from "@/components/pipeline/connection/ConnectionTemplate.vue";
import ReroutePin from "@/components/pipeline/connection/ReroutePin.vue";
import PickedConTemplate from "@/components/editor/PickedConTemplate.vue";
import OpStepNotification from "@/components/features/debugger/OpStepNotification.vue";
import SnappingLine from "@/components/editor/SnappingLine.vue";
import EditorNotification from "@/components/editor/EditorNotification.vue";
import {ContextMenuType} from "@/scripts/editor/ContextMenu";
import CreateOpCM from "@/components/editor/contextMenu/CreateOpCM.vue";
import ObjectCM from "@/components/editor/contextMenu/ObjectCM.vue";

export default {
  components: {
    EditorNotification,
    SnappingLine,
    OpStepNotification,
    PickedConTemplate,
    ReroutePin,
    ConnectionTemplate,
    OperatorTemplate, GroupTemplate, HeatmapOp, Heatmap},

  computed: {
    contextMenuTemplate() {
      return this.editor.contextMenu.type === ContextMenuType.MAIN_MENU ? CreateOpCM : ObjectCM
    },

    /** @type {SvEditor} **/
    editor() {
      return this.$streamvizzard.editor;
    }
  },

  data() {
    return {
      scrollIntensity: 0.1,
      selectBox: null,
    }
  },

  methods: {
    _onPointerMove(e) {
      const { clientX, clientY } = e;

      const rect = this.$refs.view.getBoundingClientRect();
      const x = clientX - rect.left;
      const y = clientY - rect.top;

      const k = this.editor.scale;

      this.editor.mouseX = x / k;
      this.editor.mouseY = y / k;
    },

    _onDragStart(mode, e) {
      this.editor.closeContextMenu();

      if(mode !== "wheel") this.editor.selectEditorObject(null); // Wheel drag does not clear selection

      let parentBox = this.$refs.viewContainer.getBoundingClientRect();

      if(mode === "left") this.selectBox = { startY: e.clientY, startX: e.clientX, x: 0, y: 0, width: 0, height: 0,
        offsetX: parentBox.left, offsetY: parentBox.top };
    },

    _onDrag(mode, e, editorDx, editorDy, clientDx, clientDy) {
      if(mode === "wheel") {
        this.editor.shiftX += clientDx;
        this.editor.shiftY += clientDy;
      } else {
        this.selectBox.width = Math.abs(this.selectBox.startX - e.clientX);
        this.selectBox.height = Math.abs(this.selectBox.startY - e.clientY);

        this.selectBox.x = Math.min(this.selectBox.startX, e.clientX);
        this.selectBox.y = Math.min(this.selectBox.startY, e.clientY);
      }
    },

    _onDragEnd(mode) {
      if(mode === "left") {
        if(this.selectBox.width !== 0 && this.selectBox.height !== 0) {
          let intersections = this.editor.findIntersectingObjs(this.selectBox.x,
              this.selectBox.y, this.selectBox.width, this.selectBox.height);

          // Select in correct order to keep existing visual ordering
          this.editor.selectEditorObject(intersections.ops.sort((a,b) => a.order - b.order).concat(intersections.pins));
        }

        this.selectBox = null;
      }
    },

    _onScroll(e) {
      e.preventDefault();

      if(!Services.EditorInputManager.canZoom()) return;

      const rect = this.$refs.view.getBoundingClientRect();

      const isNegative = e.deltaY < 0;

      const delta = isNegative ? this.scrollIntensity : - this.scrollIntensity;

      const ox = (rect.left - e.clientX) * delta;
      const oy = (rect.top - e.clientY) * delta;

      const oldScale = this.editor.scale;
      const newScale = oldScale * (1 + delta);
      const d = (oldScale - newScale) / (oldScale - newScale);

      this.editor.scale = newScale
      this.editor.shiftX += ox * d;
      this.editor.shiftY += oy * d;
    },

    _onContextMenu(e) {
      e.stopPropagation();
      e.preventDefault();

      this.editor.openMainContextMenu(e.clientX, e.clientY);
    },

    _onPointerOver() {
      this.editor.mouseOver = true;
    },

    _onPointerOut() {
      this.editor.mouseOver = false;
    }
  },

  mounted() {
    this.editor.viewConnector.connect((identifier) => {
      if (identifier === "dimensions") {
        let containerDims = this.$refs.viewContainer.getBoundingClientRect();
        let viewDims = this.$refs.view.getBoundingClientRect();

        return { container: containerDims, view: viewDims};
      }
    });
  }
}

</script>

<style scoped>

#editor {
  position: absolute;
  touch-action: none;
  overflow: hidden;
  width: 100%;
  height: 100%;
}

#viewContainer {
  width: 100%;
  height: 100%;
}

#view {
  transform-origin: 0 0 0;
}

.editorContainer {
  width: 100%;
  height: 100%;
  touch-action: none;
  position: absolute;
}

.editorElm {
  touch-action: none;
  position: absolute;
}

.editorGroup {
  z-index: -10; /* May be leveraged to op level on drag */
}

.editorSnappingLine {
  z-index: -5;
}

.editorCon {
  z-index: -1;
}

.editorOp {
  z-index: 0; /* Calculated based on op order (>= 0) */
}

.selectBox {
  pointer-events: none;
  border: 2px solid var(--main-font-color);
  border-radius: var(--window-border-radius);
  position: absolute;
}

.controlInfo {
  position: absolute;
  bottom: 6px;
  background: white;
  color: var(--main-hover-color);
  pointer-events: none;
  border: 1px solid var(--main-border-color);
  border-radius: var(--button-border-radius);
  font-size: 0.85em;
  padding: 0 4px 0 2px;
}

</style>
