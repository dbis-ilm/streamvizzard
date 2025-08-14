<template>
  <div>
    <div class="formInputContainer">
      <span class="formInputLabel limitedText alignLeft" title="Processed tuples per second">Throughput:&nbsp;</span>
      <FormInputWithUnit :class="(targetStats['autoTp'] ? 'disabled' : '')" :type="'text'" :readonly="false" v-model="targetStats['targetTp']" :unit="'tuples / s'" :unitWidth="'80px'"></FormInputWithUnit>
      <div class="autoSelect" title="Auto, if this value should be derived by the compiler">
        Auto:&nbsp;<input type="checkbox" :checked="targetStats['autoTp']" @change="_onAutoCheck('autoTp', $event)"/>
      </div>
    </div>
    <div class="formInputContainer">
      <span class="formInputLabel limitedText alignLeft" title="Operator single-node execution time per tuple">Execution <span class="dataSource" :title="'Source of information: ' + _getExInformationSource()">{{ _getExInformationSource().charAt(0) }}</span> :&nbsp;</span>
      <FormInputWithUnit :class="(targetStats['autoExTime'] ? 'disabled' : '')" :type="'text'" :readonly="false" v-model="targetStats['targetExTime']" :unit="'ms'" :unitWidth="'35px'"></FormInputWithUnit>
      <div class="autoSelect" title="Auto, if this value should be derived by the compiler">
        Auto:&nbsp;<input type="checkbox" :checked="targetStats['autoExTime']" @change="_onAutoCheck('autoExTime', $event)"/>
      </div>
    </div>
  </div>
</template>

<script>


import FormInputWithUnit from "@/components/interface/elements/base/FormInputWithUnit.vue";

export default {
  name: 'CompileTargetStats',
  components: {FormInputWithUnit},
  props: ["node", "targetStats"],

  methods: {
    _onAutoCheck(key, e) {
      this.targetStats[key] = e.target.checked
    },

    _getExInformationSource() {
      if(!this.targetStats['autoExTime']) return "Manual"
      else return this.targetStats['exTimeSource']
    }
  },
}

</script>

<style>

.dataSource {
  background: var(--main-border-color);
  border-radius: var(--button-border-radius);
  min-width: 20px;
  display: inline-block;
  text-align: center;
}

</style>

<style scoped>

hr {
  color: var(--main-border-color);
}

.formInputLabel {
  width: 110px;
}

.autoSelect {
  align-content: center;
  padding-left: 5px;
  width: 100px;
  flex: 0 0 content;
}

</style>