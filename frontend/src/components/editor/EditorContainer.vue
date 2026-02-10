<template>
  <div id="editor">
    <div id="viewContainer" ref="viewContainer" @pointermove.capture="_onPointerMove" @wheel="_onScroll" @contextmenu="_onContextMenu"
         @pointerover="_onPointerOver" @pointerout="_onPointerOut" v-draggable="{dragStart: this._onDragStart, dragging: this._onDrag}">
      <div id="view" ref="view" :style="'transform: translate(' + editor.shiftX + 'px, ' + editor.shiftY + 'px) scale(' + editor.scale + ')'">
          <div class="editorContainer heatmaps" style="z-index: 0;">
            <HeatmapOp v-show="$streamvizzard.monitor.isHeatmapActive()" v-for="op in $streamvizzard.pipeline.operators"
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

            <OpStepOverlay v-show="$streamvizzard.debugger.enabled" v-for="op in $streamvizzard.pipeline.operators.filter((o) => o.debugStepNotification != null)"
                           :key="op.debugStepNotification.getUniqueKey()" :stepEx="op.debugStepNotification" :operator="op" class="editorElm"/>
          </div>
      </div>
    </div>

    <Heatmap v-if="$streamvizzard.monitor.isHeatmapActive()" :hmType="$streamvizzard.monitor.heatmapType"/>

    <Menu v-if="editor.contextMenu" :menu="editor.contextMenu" :key="editor.contextMenu.id" :delay="50"/>
  </div>
</template>

<script>

import Heatmap from "@/components/features/monitor/heatmap/Heatmap.vue";
import Menu from "@/plugins/context-menu-plugin/menu/Menu.vue";
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

export default {
  components: {
    EditorNotification,
    SnappingLine,
    OpStepOverlay: OpStepNotification,
    PickedConTemplate,
    ReroutePin,
    ConnectionTemplate,
    OperatorTemplate, GroupTemplate, HeatmapOp, Menu, Heatmap},

  computed: {
    /** @type {SvEditor} **/
    editor() {
      return this.$streamvizzard.editor;
    }
  },

  data() {
    return {
      scrollIntensity: 0.1,
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

    _onDragStart() {
      this.editor.closeContextMenu();
      this.editor.selectOperator(null);
    },

    _onDrag(e, editorDx, editorDy, clientDx, clientDy) {
      this.editor.shiftX += clientDx;
      this.editor.shiftY += clientDy;
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

</style>