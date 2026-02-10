<template>
  <div style="height:100%; width:100%;" class="dataMonitor">
    <component v-if="operator.monitor.displayMode != null" :is="operator.monitor.displayMode.template.component"
               class="dt" :value="operator.monitor.displayData" :settings="displayModeSettings" :operator="operator"/>
  </div>
</template>

<script>
import SvOperator from "@/scripts/pipeline/operators/SvOperator";

export default {
  props: {
    operator: {type: SvOperator, required: true},
  },

  data() {
    return {
      currentTemplate: null,
      currentDisplayElement: null,
      currentDisplayVariant: null,

      displayMode: 0,
      dataType: null,
      displaySocket: 0,

      dataStructure: null, //The structure of the data
      dataInspect: null, //The inspect command from UI

      settings: null
    }
  },

  computed: {
    displayModeSettings() {
      if(this.operator.monitor.displayMode == null) return {};
      return this.operator.monitor.displayMode.getSafeSettings(this.operator.monitor.displayModeSettings);
    }
  }
}
</script>

<style scoped>

.dt {
  margin-bottom: 4px;
}

</style>
