<template>
  <div :style="'width: ' + width + '; height: ' + height + 'px;'">
    <slot></slot>
  </div>
</template>

<script>

import $ from "jquery";
import {Services} from "@/scripts/services/Services";
import {safeVal} from "@/scripts/tools/Utils";

export default {
  props: {
    /** @type {SvOperator} **/
    operator: {required: true},
    autoHide: {type: Boolean, required: true},
    resizeKey: {type: String, required: true},
  },

  computed: {
    height() {
      let height = safeVal(this.operator.resizeElemHeights[this.resizeKey]);

      return height == null ? "" : (height + "px;");
    },

    width() {
      return this.operator.resizeElmWidth != null ? (this.operator.resizeElmWidth + "px;") : "";
    }
  },

  mounted() {
    let jqElement = $(this.$el);

    jqElement.parent().addClass("resizableCtrl");

    let op = this.operator;
    let key = this.resizeKey;

    jqElement.resizable({
      autoHide: this.autoHide,

      start: function() {
        Services.EditorInputManager.onInputSelected(jqElement);
      },

      stop: function() {
        Services.EditorInputManager.onInputDeselected();
      },

      resize(event, ui){
        event.originalEvent.stopPropagation();
        event.originalEvent.preventDefault();
        event.stopPropagation();
        event.preventDefault();

        op.resizeElement(key, ui.size.width, ui.size.height);
      }
    });
  }
}
</script>
