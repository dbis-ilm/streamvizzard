<template>
  <div :title="tooltip" ref="container" class="controlContainer codeContainer" style="min-width:250px; min-height: 100px; width: 250px; height: 100px; position: relative;" v-if="ctrl.show">
    <div class="codeHeader">Custom Python Code<i class="bi bi-info-circle codeInfo" :title="codeInfoTooltip"></i></div>
    <i class="bi bi-info-circle codeChangedDataInfo" v-if="hasChangedData" title="Unchanged data will be applied when deselecting the textarea."></i>
    <ace-editor class="codeBody" :title="hasChangedData ? 'Unchanged data will be applied when deselecting the textarea.' : ''" ref="editor" :value="value" @init="editorInit" @input="valueInput" lang="python" theme="github" style="width: 100%; height:100%;"></ace-editor>
    </div>
</template>

<script>

import {makeResizable} from "@/scripts/tools/Utils";
import $ from "jquery";
import {EditorInputManager} from "@/scripts/services/EditorInputManager";
import {CodeControl} from "@/scripts/components/modules/base/controls/CodeCtrl";

export default {
  props: ['readonly', 'cKey', 'defaultVal', 'tooltip', 'description', 'node', 'ctrl', 'type'],
  data() {
    return {
      editor: null,
      value: '',
      oldValue: ''
    }
  },
  methods: {
    valueInput(content) {
      this.value = content;
    },

    update() {
      if(!this.hasChangedData) return;

      this.setData(this.value);
    },

    setData(data) {
      this.value = data;

      let oldValue = this.oldValue;

      this.oldValue = this.value;

      if(oldValue !== this.value) this.node.component.onControlValueChanged(this.ctrl, this.node, oldValue);

      // Instance update + delayed update

      this.node.component.editor.view.updateConnections({ node: this.node });

      setTimeout(() => {
        this.node.component.editor.view.updateConnections({ node: this.node });
      }, 10);
    },

    editorInit: function (editor) {
      this.editor = editor;

      require('ace-builds/src-min-noconflict/ext-language_tools');
      require('ace-builds/src-min-noconflict/mode-python');
      require('ace-builds/src-min-noconflict/theme-github');
      editor.session.setMode("ace/mode/python");
      editor.setOptions({
        minLines: 3,
        fontSize: 14,
        highlightActiveLine: true,
        showLineNumbers: true,
        tabSize: 4,
        showPrintMargin: false,
        showGutter: true,
        autoScrollEditorIntoView: true,
        hasCssTransforms: true,
        dragEnabled: false
      });

      editor.resize();

      this.$refs.editor.$el.classList.add("editorInput"); // Add EditorInputManager functionality

      this.$refs.editor.$el.addEventListener("focusout", function() {
        editor.session.selection.clearSelection();
      });
    },

    onResize () {
      this.editor.resize();
    }
  },
  computed: {
    codeInfoTooltip() {
      if(this.type === CodeControl.CodeType.UDF)
        return "Supports arbitrary Python code and imports which will be executed from top to bottom. " +
            "Must return a Python tuple with a value for each output socket. " +
            "Input data will be passed in an 'input' Python tuple which contains a value for each input socket.";
      else if(this.type === CodeControl.CodeType.FILTER)
        return "Supports arbitrary Python code and imports which will be executed from top to bottom. " +
            "Must return a boolean which signals if the tuple should be filtered (false) or passed to the next operator (true). " +
            "Input data will be passed in an 'input' Python tuple which contains a value for each input socket.";
      else if(this.type === CodeControl.CodeType.UDO)
        return "Supports arbitrary Python code and imports in a structured class-based way.";
      return "";
    },

    hasChangedData(){
      return this.oldValue !== this.value;
    }
  },
  mounted() {
    this.oldValue = this.defaultVal;
    this.value = this.defaultVal;

    this.resizeObserver = new ResizeObserver(this.onResize);
    this.resizeObserver.observe(this.$refs.container);

    makeResizable($(this.$refs.container), this.node, this.cKey, false);

    let ths = this;
    this.editor.on("blur", function() {
      ths.update();
    });

    // Only allow mouse-scroll if this input is selected
    this.editor.on("mousewheel", function(e) {
      if(!EditorInputManager.isElementSelected(ths.$refs.editor.$el)) e.preventDefault();
    });
  },

  beforeDestroy() {
    this.resizeObserver.unobserve(this.$refs.container);
  }
}

</script>

<style scoped>

.codeChangedDataInfo {
  color: darkorange;
  position: absolute;
  right: 1px;
  font-size: 12px;
  top: 1px;
}

.codeContainer {
  display: flex;
  flex-direction: column;
}

.codeHeader {
  color: #8F8F9D;
  text-align: center;
  flex: 0;
  font-size: 12px;
  width: 100%;

  padding-bottom: 2px;
  margin-bottom: -2px;

  border: 1px solid #8F8F9D;
  background: #efefef;
  border-radius: 2px 2px 0 0;
}

.codeInfo {
  padding-left: 5px;
}

.codeBody {
  flex: 1;
}



</style>

<style>

.ace_editor {
  border-radius: 2px;
  border: 1px solid #8F8F9D;
}

.ace_editor, .ace_editor *{
  font-family: "Monaco", "Menlo", "Ubuntu Mono", "Droid Sans Mono", "Consolas", monospace !important;
}

.ace_editor .ace_gutter {
  background: #efefef !important;
}

</style>
