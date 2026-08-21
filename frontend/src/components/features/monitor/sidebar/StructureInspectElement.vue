<template>
  <div :class="[!rootEntry && 'inspectContainer']">
    <div :class="['inspectElement', 'noSelect', selected && 'selected']" @click="selectElement()">
      <span class='inspectElementToggle' v-show="hasChildren">{{ visible ? '-' : '+'}}</span>
      <span class='inspectElementKey limitedText' >{{ data['name'] }}</span>
      <span class="inspectElementType">{{ data['dataType'] }}</span>
    </div>

    <div :class="[hasChildren && visible && 'nestedInspectGroup']">
      <StructureInspectElement v-for="entry in data['children']" v-show="visible"
                               :key="entryKey + '>' + entry['name']"
                               :entryKey="entryKey + '>' + entry['name']"
                               :parentKey="entryKey"
                               :data="entry" :operator="operator" />
    </div>

    <div class="inspectContainer inspectElement disabled noSelect" v-show="visible" v-if="data['omitted'] > 0" style="margin-bottom: 10px;">
      <i>[{{ data['omitted'] }} element(s) were omitted]</i>
    </div>
  </div>

</template>

<script>

import SvOperator from "@/scripts/pipeline/operators/SvOperator";

export default {
  name: "StructureInspectElement",
  props: {
    parentKey: {type: String, required: false},
    entryKey: {type: String, required: true},
    data: {type: Object, required: true},
    operator: {type: SvOperator, required: true},
  },

  computed: {
    rootEntry() {
      return this.parentKey == null;
    },

    hasChildren() {
      return this.data['children'].length > 0;
    },

    visible() {
      return (this.operator.monitor.displayDataInspect && this.operator.monitor.displayDataInspect.includes(this.entryKey)) || this.selected;
    },

    selected() {
      return this.operator.monitor.displayDataInspect === this.entryKey;
    }
  },

  methods: {
    selectElement() {
      if(this.selected && !this.rootEntry) this.operator.monitor.updateDisplayDataInspect(this.parentKey);
      else this.operator.monitor.updateDisplayDataInspect(this.entryKey);
    },
  }
}
</script>

<style scoped>

.inspectContainer {
  padding-left: 15px;
}

.inspectElement {
  display: flex;
  flex-direction: row;
  text-align: left;

  cursor: pointer;
}
.inspectElementKey {
  flex: 1 1 100%;
}

.inspectElement.selected {
  font-weight: bold;
}

.nestedInspectGroup {
  border-left: 1px solid var(--second-border-color);
  margin-left: 2px;
}

.inspectElementToggle {
  width: 20px;
}

.inspectElementType {
  text-align: right;
  font-style: italic;
  width: 75px;

  margin-right: 5px;
}

</style>
