<template>
<div class="frame-comment">
  <div class="ctrlRow">
    <!--<span ref="cp" class="colorPicker"></span>-->
    <div style="height: 100%;"><input ref="nameInput" type="text" :value="frame.text" @change="onNameChange($event)" class="nameInput editorInput"></div>
    <div style="right: -6px; top: -6px; position:absolute;">
      <i ref="collapseIcon" class="ctrlIcon bi bi-eye" title="Collapse / Expand all Nodes" @click="onCollapse()"></i>
      <i class="ctrlIcon bi bi-x-circle" title="Remove Group" @click="onRemove()"></i>
    </div>
  </div>
</div>
</template>

<script>
import $ from 'jquery';
//import Huebee from "huebee";
import {makeNameInput, registerAutoBorderSize} from "@/scripts/tools/Utils";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";

export default {
  name: "FrameTemplate",
  props: ["frame"],
  methods: {
    onRemove: function() {
      this.frame.editor.trigger("removecomment", {"comment": this.frame, "type": "frame"});
    },

    onCollapse: function() {
      let hidden = this.$el.classList.contains("collapsed");

      if(hidden) this.setCollapsed(false);
      else this.setCollapsed(true);
    },

    setCollapsed(collapsed, triggerNode = true) {
      if(collapsed) {
        this.frame.collapse(triggerNode);
        this.$el.classList.add("collapsed");
        this.$refs.collapseIcon.classList.remove("bi-eye");
        this.$refs.collapseIcon.classList.add("bi-eye-slash");
      } else {
        this.frame.expand(triggerNode);
        this.$el.classList.remove("collapsed");
        this.$refs.collapseIcon.classList.add("bi-eye");
        this.$refs.collapseIcon.classList.remove("bi-eye-slash");
      }

      executeEvent(EVENTS.GROUP_COLLAPSED, [this.frame, collapsed]);
    },

    onNameChange(event) {
      let prev = this.frame.text;

      this.frame.text = event.target.value;

      executeEvent(EVENTS.GROUP_NAME_CHANGED, [this.frame, prev]);
    }
  },

  mounted() {
    let thisEl = this;
    let el = $(this.$el);

    makeNameInput($(this.$refs.nameInput), $(this.$refs.nameInput).closest("div"), "disabled");

    registerAutoBorderSize(this.$el, 2);

    el.resizable({
      autoHide: true,
      handles: "all",
      start: function() {
        el.addClass("editorInput");
      },
      stop: function() {
        el.removeClass("editorInput");

        thisEl.frame.afterSizeChangedFinished();
      },
      resize: function(event, ui) {
        thisEl.frame.updateSize(ui.size.width, ui.size.height);
      }
    });

    /*let huebee = new Huebee( thisEl.$refs.cp, {
      setBGColor: false,
      setText: false,
      saturations: 1,
      shades: 0,
      grayCount: 0,
      customColors: ['#0F58FF', '#ff595e', '#ffca3a', '#8ac926', '#1982c4', '#6a4c93']
    });

    huebee.on( 'change', function( color) {
      let rgb = hexToRgb(color);
      thisEl.$el.style.background = "rgba(" + rgb.r + "," + rgb.g + "," + rgb.b + "," + 0.2 + ")";
    })*/
  }
}
</script>

<style>
.frame-comment {
  padding: 12px;
  position: absolute !important;
  cursor:move;
  border-radius: 16px;

  /*background: rgba(62, 146, 255, 0.2);
  border: 2px solid #9abdff;
  background: rgba(200, 200, 200, 0.35);*/

  background: rgba(247, 247, 247, 0.7);
  border: 2px solid #828282;

  z-index: -10;
}

.heatmapActive .frame-comment  {
  background: none;
  border: 2px solid #8282822e;
}

.frame-comment .nameInput {
  cursor: pointer;
  border:none;
  background-image:none;
  background-color:transparent;
  -webkit-box-shadow: none;
  -moz-box-shadow: none;
  box-shadow: none;

  /* color: #7a96ca; */
  color: #555;
  font-weight: bold;

  text-align: left;
  top: -6px;
  left: 0;
  position: absolute;
  font-size: 26px;
  height: 100%;

  width:calc(100% - 80px);
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.frame-comment .nameInput:focus {
  outline: none;
}

.frame-comment .colorPicker {
  cursor: pointer;
  display:block;
  width: 10px;
  height: 10px;
  background: white;
}

.frame-comment .huebee__container, .frame-comment .huebee__canvas {
  width: 200px !important;
  height: 40px !important;
  max-width: 200px !important;
  max-height: 200px !important;
}

.frame-comment .huebee__container {
  background: #777;
  border: 5px solid #222;
  border-radius: 8px;
}

.frame-comment .huebee {
  position: absolute;
  top: -60px !important;
  cursor:pointer;
}

</style>
