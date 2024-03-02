<template>
  <div :title="tooltip" ref="container" class="controlContainer" style="min-width:250px; min-height: 100px; width: 250px; height: 100px; position: relative;">
    <ace-editor :class="'mouseEventBlocker'" :title="hasChangedData ? 'Unchanged data will be applied when deselecting the textarea.' : ''" ref="editor" :value="value" @init="editorInit" @input="valueInput" lang="python" theme="github" style="width: 100%; height:100%;"></ace-editor>
    <i class="bi bi-info-circle codeChangedDataInfo" v-if="hasChangedData" title="Unchanged data will be applied when deselecting the textarea."></i>
  </div>
</template>

<script>

import {makeResizable} from "@/scripts/tools/Utils";
import $ from "jquery";

export default {
  props: ['readonly', 'emitter', 'ikey', 'getData', 'putData', 'defaultVal', 'tooltip', 'description', 'node', 'ctrl'],
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

      if (this.ikey) this.putData(this.ikey, this.value);

      this.node.component.onControlValueChanged(this.ctrl, this.node, oldValue);

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
        showLineNumbers: false,
        tabSize: 4,
        showPrintMargin: false,
        showGutter: false,
        autoScrollEditorIntoView: true,
        hasCssTransforms: true
      });

      editor.resize();
    },

    onResize () {
      this.editor.resize();
    }
  },
  computed: {
    hasChangedData(){
      return this.oldValue !== this.value;
    }
  },
  mounted() {
    this.oldValue = this.defaultVal;
    this.value = this.defaultVal;

    this.resizeObserver = new ResizeObserver(this.onResize);
    this.resizeObserver.observe(this.$refs.container);

    makeResizable($(this.$refs.container), this.node, this.ikey, false);

    let ths = this;
    this.editor.on("blur", function() {
      ths.update();
    });
  },

  beforeDestroy() {
    this.resizeObserver.unobserve(this.$refs.container);
  }
}

</script>

<style scoped>

.codeChangedDataInfo{
  color:darkorange;
  position: absolute;
  right: 2px;
  top: -1px;
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

</style>
