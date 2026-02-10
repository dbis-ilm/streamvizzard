<template>
  <div class="container">
    <div class="title">
      Display Transformer
      <i class="bi bi-x-circle clickableIcon removeIcon" title="Remove transformer" @click="clearTransformer"></i>
    </div>
    <div class="codeContainer">
      <div class="codeHeader">Custom Python Code<i class="bi bi-info-circle codeInfo" :title="codeTooltip"></i></div>
      <i class="bi bi-info-circle codeChangedDataInfo" v-if="hasChangedData" title="Unchanged data will be applied when deselecting the textarea."></i>
      <ace-editor class="codeBody" ref="editor" :value="value" @init="editorInit" @input="valueInput" lang="python" theme="github"></ace-editor>
      <div></div>
    </div>

  </div>
</template>

<script>

import {valueOr} from "@/scripts/tools/Utils";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";

export default {
  name: "DataTransformer",
  props: {
    operator: {type: SvOperator, required: true},
  },

  data() {
    return {
      oldValue: "",
      value: "",

      codeTooltip: "Supports arbitrary Python code and imports which will be executed from top to bottom.\n" +
          "Input data of the selected display socket will be passed in an 'input' Python object.\n" +
          "Must return a single Python value/object as a result to display."
    }
  },

  watch: {
    "operator.monitor.displaySocket"() {
      this.initializeOp();
    },

    operator() {
      this.initializeOp();
    },
  },

  computed: {
    hasChangedData(){
      return this.oldValue !== this.value;
    }
  },

  methods: {
    editorInit: function (editor) {
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

      editor.renderer.setScrollMargin(0, 10, 0, 0);
      editor.resize();

      this.$refs.editor.$el.addEventListener("focusout", function() {
        editor.session.selection.clearSelection();
      });

      let ths = this;
      editor.on("blur", function() {
        ths.update();
      });
    },

    initializeOp() {
      this.value = valueOr(this.operator.monitor.displayDataTransformer[this.operator.monitor.displaySocket], "return input");
      this.oldValue = this.value;
    },

    clearTransformer() {
      this.applyData("");
    },

    update() {
      if(!this.hasChangedData) return;

      this.applyData(this.value);
    },

    applyData(data) {
      data = data.trim();

      let storedVal;
      if(data == null || data.length === 0 || data === "return input") storedVal = null;
      else storedVal = data;

      this.value = storedVal == null ? "return input" : storedVal;
      this.oldValue = this.value;

      this.operator.monitor.updateDisplayDataTransformer(this.operator.monitor.displaySocket, storedVal);
    },

    valueInput(content) {
      this.value = content;
    },
  },

  mounted() {
    this.initializeOp();
  }
}
</script>

<style scoped>

.title {
  text-decoration: underline;
  position: relative;
}

.removeIcon {
  position: absolute;
  padding-left: 5px;
}

.codeContainer {
  width: 100%;
  height:138px;
  margin-top: 12px;
  position: relative;
  display: flex;
  flex-direction: column;
}

.codeHeader {
  color: var(--main-hover-color);
  text-align: center;
  font-size: 12px;
  width: 100%;

  padding-bottom: 2px;
  margin-bottom: -2px;

  border: 1px solid var(--second-border-color);
  background: #efefef;
  border-radius: 2px 2px 0 0;
  box-sizing: border-box;
}

.codeChangedDataInfo {
  color: var(--warning-color);
  position: absolute;
  right: 3px;
  font-size: 12px;
  top: 1px;
}

.codeInfo {
  padding-left: 5px;
}

.codeBody {
  width: 100%;
  height:100%;
  border-radius: 2px;
  border: 1px solid var(--second-border-color);
  background: var(--second-border-color);
  box-sizing: border-box;
}

</style>
