<template>
  <ResizeElement :resizeKey="'DT'" :autoHide="true" :operator="operator"
                 class="tableDt limitedText" ref="display">
    <table>
      <tr v-if="showHeader"><th v-for="head in tableHeader" :key="head">{{head}}</th></tr>
      <tr v-for="(row,idx) in tableData" :key="String(row)+idx"><td v-for="(entry,idx) in row" :key="String(entry)+idx">{{entry}}</td></tr>
    </table>

  </ResizeElement>
</template>

<script>

import ResizeElement from "@/components/pipeline/operator/ResizeElement.vue";
import {valueOr} from "@/scripts/tools/Utils";

export default {
  components: {ResizeElement},
  inject: ['performTrackedRender'],
  props: {
    /** @type {SvOperator} **/
    operator: {required: true},
    settings: {type: Object, required: true},
    value: {required: true},
  },

  data() {
    return {
      showHeader: true,
      tableHeader: [],
      tableData: [],
    }
  },

  watch: {
    value() {
      this.performTrackedRender(() => {
        this._updateDisplayValue(this.value)
      });
    }
  },

  methods: {
    _updateDisplayValue(data) {
      data = valueOr(data, null);

      if(data == null) {
        this.tableHeader = [];
        this.tableData = [];
      } else {
        this.tableHeader = data.keys;
        this.tableData = data.entries;
      }
    },
  },

  mounted() {
    this._updateDisplayValue(this.value);
  }
}
</script>

<style scoped>

.tableDt {
  min-width: 200px;
  min-height: 3.5em;

  text-align:center;
}

.tableDt table {
  margin: 0 auto;
  border-spacing: 10px 0;
}

</style>
