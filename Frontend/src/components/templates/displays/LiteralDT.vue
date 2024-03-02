<template>
  <div class="literalDp" ref="display" :title="displayValue">{{ displayValue }}</div>
</template>

<script>

import StringDS from "@/components/templates/displays/settings/StringDS";
import SelectDS from "@/components/templates/displays/settings/SelectDS";
import {safeVal} from "@/scripts/tools/Utils";

export default {
  props: ['value', 'control'],
  data() {
    return {
      displayValue: "",

      exp: null,
      maxLength: null,
      styleMap: []
    }
  },

  methods: {
    setValue(value) {
      this.value = value;

      this._updateDisplayValue();
    },

    setSettings(props) {
      this.exp = props.exp !== undefined ? props.exp : null;
      this.maxLength = props.maxLength !== undefined ? props.maxLength : null

      // Clear old styles
      for(let s of this.styleMap) this.$refs.display.style.removeProperty(s);
      this.styleMap = [];

      // Apply css styles
      if(props.style !== undefined) {
        let styleSplit = props.style.split(";");

        try {
          for(let s of styleSplit) {
            let ss = s.split(":");
            if(ss.length !== 2) continue;

            let styleName = ss[0].trim();
            this.$refs.display.style.setProperty(styleName, ss[1].trim());
            this.styleMap.push(styleName);
          }
        } catch(_) {
          //Ignore
        }
      }

      if(props.align !== undefined) this.$refs.display.style.textAlign = props.align;
      else this.$refs.display.style.textAlign = null;

      this._updateDisplayValue();
    },

    _updateDisplayValue() {
      //if(this.exp != null) this.displayValue = this.exp.replace("$VAL", this.value);
      if(this.exp != null && this.value != null) {
        try { this.displayValue = (new Function("return " + this.exp.replace("$VAL", "'" + this.value + "'") + ";")()); }
        catch(_) {
          //ignore
        }
      } else this.displayValue = this.value;

      if(this.maxLength != null && this.maxLength > 0 && this.displayValue != null) this.displayValue = this.displayValue.substring(0, this.maxLength);
    },

    getSettingsOptions(props, propsDef) {
      return [{"key": "exp", "name": "Expression", "value": safeVal(props.exp, "$VAL"), "desc": "How to display the value. $VAL signals the value to display. " +
            "JS code can be used but needs to return a string.\nExample: \"Value: \" + $VAL.toUpperCase()", "default": safeVal(propsDef.exp, "$VAL"), "template": StringDS},
        {"key": "maxLength", "name": "Max Length", "value": props.maxLength, "desc": "How many characters the display string will have at most", "default": propsDef.maxLength, "template": StringDS},
        {"key": "style", "name": "Style", "value": props.style, "desc": "Css style of the display text. Separate multiple values with ';'\nExample: font-weight:bold; font-size:24px;", "default": propsDef.style, "template": StringDS},
        {"key": "align", "name": "Alignment", "value": safeVal(props.align, "Center"), "data": ["Center", "Left", "Right"], "desc": "Alignment of the display text", "default": safeVal(propsDef.align, "Center"), "template": SelectDS}];
    },
  },

  mounted() {}
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
