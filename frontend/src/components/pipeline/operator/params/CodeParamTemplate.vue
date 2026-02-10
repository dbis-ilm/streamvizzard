<template>
  <ResizeElement :resizeKey="param.key" :autoHide="true" :operator="param.operator"
                 :title="param.tooltip" class="controlContainer codeContainer editorInput">
    <div class="codeHeader">Custom Python Code<i class="bi bi-info-circle codeInfo" :title="codeInfoTooltip"></i></div>
    <i class="bi bi-info-circle codeChangedDataInfo" v-if="hasChangedData" title="Unchanged data will be applied when deselecting the textarea."></i>
    <ace-editor class="codeBody" :title="hasChangedData ? 'Unchanged data will be applied when deselecting the textarea.' : ''" ref="editor"
                :value="value" @init="editorInit" @input="valueInput" lang="python" theme="github"></ace-editor>
    </ResizeElement>
</template>

<script>

import {Services} from "@/scripts/services/Services";
import {CodeParam} from "@/scripts/pipeline/operators/modules/base/params/CodeParam";
import ResizeElement from "@/components/pipeline/operator/ResizeElement.vue";

export default {
  components: {ResizeElement},
  props: {
    /** @type CodeParam **/
    param: {required: true},
  },

  data() {
    return {
      editor: null,
      value: ""
    }
  },

  watch: {
    "param.value"() {
      this.value = this.param.value;
    }
  },

  methods: {
    valueInput(content) {
      this.value = content;
    },

    update() {
      if(!this.hasChangedData) return;

      this.param.setValue(this.value);
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

      editor.renderer.setScrollMargin(0, 10, 0, 0);
      editor.resize();

      //this.$refs.editor.$el.classList.add("editorInput"); // Add EditorInputManager functionality

      this.$el.addEventListener("deactivate", function() {
        editor.session.selection.clearSelection();
      });

      this.$el.addEventListener("activate", function() {
        editor.focus();
      });

      this.$el.addEventListener("keydown", (e) => {
        // Block enter propagation since this deselects input by default (but here creates new line)
        if(e.key === "Enter") e.stopPropagation();
      });
    },

    onResize () {
      this.editor.resize();
    }
  },

  computed: {
    codeInfoTooltip() {
      if(this.param.type === CodeParam.CodeType.UDF)
        return "Supports arbitrary Python code and imports which will be executed from top to bottom. " +
            "Must return a Python tuple with a value for each output socket. " +
            "Input data will be passed in an 'input' Python tuple which contains a value for each input socket.";
      else if(this.param.type === CodeParam.CodeType.FILTER)
        return "Supports arbitrary Python code and imports which will be executed from top to bottom. " +
            "Must return a boolean which signals if the tuple should be filtered (false) or passed to the next operator (true). " +
            "Input data will be passed in an 'input' Python tuple which contains a value for each input socket.";
      else if(this.param.type === CodeParam.CodeType.UDO)
        return "Supports arbitrary Python code and imports in a structured class-based way.";
      return "";
    },

    hasChangedData(){
      return this.param.value !== this.value;
    }
  },

  mounted() {
    this.value = this.param.value;

    this.resizeObserver = new ResizeObserver(this.onResize);
    this.resizeObserver.observe(this.$el);

    this.editor.on("blur", () => {
      this.update();
    });

    // Only allow mouse-scroll if this input is selected
    this.editor.on("mousewheel", (e) => {
      if(!Services.EditorInputManager.isElementSelected(this.$el)) e.preventDefault();
    });
  },

  beforeDestroy() {
    this.resizeObserver.unobserve(this.$el);
  }
}

</script>

<style scoped>

.codeChangedDataInfo {
  color: var(--warning-color);
  position: absolute;
  right: 2px;
  font-size: 12px;
}

.codeContainer {
  display: flex;
  flex-direction: column;

  min-width: 250px;
  min-height: 100px;
  width: 250px;
  height: 100px;
  position: relative;
}

.codeHeader {
  color: var(--main-hover-color);
  text-align: center;
  flex: 0;
  font-size: 12px;
  width: 100%;

  padding-bottom: 2px;

  box-shadow: 0 0 0 calc(1px * var(--editor-scale-fac)) var(--second-border-color);
  background: #efefef;
  border-radius: 2px 2px 0 0;
}

.codeInfo {
  padding-left: 5px;
}

.codeBody {
  flex: 1;
  border-radius: 0 0 2px 2px;
  box-shadow: 0 0 0 calc(1px * var(--editor-scale-fac)) var(--second-border-color);
  background: var(--second-border-color);
  width: 100%;
  height:100%;
}

</style>

<style>

/* Only show text cursor when selected, otherwise pointer */

.codeBody .ace_scroller {
  cursor: pointer;
}

.editorInput.codeContainer[ei-active] .codeBody .ace_scroller {
  cursor: text;
}

/* Add bigger outline and background color on selected */

.editorInput.codeContainer[ei-active] .codeBody {
  box-shadow: 0 0 0 calc(2px * var(--editor-scale-fac)) var(--main-font-color);
}

.editorInput.codeContainer[ei-active] .codeHeader {
  background: var(--input-active-color);

  color: var(--main-font-color) !important;
  text-shadow: -0.01ex 0 0 var(--main-font-color), 0.01ex 0 0 var(--main-font-color) !important;

  box-shadow: 0 0 0 calc(2px * var(--editor-scale-fac)) var(--main-font-color);
}

</style>
