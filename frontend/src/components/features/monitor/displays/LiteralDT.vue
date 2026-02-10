<template>
  <ResizeElement :resizeKey="'DT'" :autoHide="true" :operator="operator"
                 class="literalDp" ref="display" :title="displayValue">{{ displayValue }}</ResizeElement>
</template>

<script>

import {valueOr} from "@/scripts/tools/Utils";
import ResizeElement from "@/components/pipeline/operator/ResizeElement.vue";

export default {
  components: {ResizeElement},
  props: {
    /** @type {SvOperator} **/
    operator: {required: true},
    settings: {type: Object, required: true},
    value: {required: true},
  },

  data() {
    return {
      displayValue: "",

      exp: null,
      maxLength: null,
      styleMap: []
    }
  },

  watch: {
    value() {
      this._updateDisplayValue(this.value);
    },

    settings: {
      handler() {
        this._applySettings(this.settings);
        this._updateDisplayValue(this.value);
      }, deep: true
    }
  },

  methods: {
    _applySettings(props) {
      this.exp = props.exp;
      this.maxLength = props.maxLength;

      // Clear old styles
      for(let s of this.styleMap) this.$refs.display.$el.style.removeProperty(s);
      this.styleMap = [];

      // Apply css styles
      if(props.style != null) {
        let styleSplit = props.style.split(";");

        try {
          for(let s of styleSplit) {
            let ss = s.split(":");
            if(ss.length !== 2) continue;

            let styleName = ss[0].trim();
            this.$refs.display.$el.style.setProperty(styleName, ss[1].trim());
            this.styleMap.push(styleName);
          }
        } catch(_) {
          //Ignore
        }
      }

      if(props.align !== undefined) this.$refs.display.$el.style.textAlign = props.align;
      else this.$refs.display.$el.style.textAlign = null;
    },

    _updateDisplayValue(data) {
      data = valueOr(data, "");

      if(this.exp != null) {
        try { this.displayValue = (new Function("return " + this.exp.replace("$VAL", "'" + data + "'") + ";")()); }
        catch(_) {
          //ignore
        }
      } else this.displayValue = data;

      if(this.maxLength != null && this.maxLength > 0 && this.displayValue != null) this.displayValue = this.displayValue.substring(0, this.maxLength);
    },
  },

  mounted() {
    this._applySettings(this.settings);
    this._updateDisplayValue(this.value);
  }
}
</script>

<style scoped>

.literalDp {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;

  min-width:200px;
  min-height: 1.5em;
  width:200px;
  height: 1.5em;

  text-align:center;
}

</style>
