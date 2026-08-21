<template>
  <div v-if="suggestions != null" class="sidebarAdvisor">
    <CollapseHeader :openedDir="'up'" class="sectionHeader" v-model="$streamvizzard.advisor.showSidebar" title="Advisions"/>
    <div class="sidebarAdvisorContent" v-show="$streamvizzard.advisor.showSidebar">
      <div v-for="(suggestion, index) in suggestions" :key="suggestion.key" style="margin-top: 10px;">
        <div><b>{{ index + 1 }})</b> {{ suggestion.message }}</div>

        <div v-if="suggestion instanceof AddOpAS">
          <v-select v-auto-blur :options="suggestion.ops" :value="null" label="name" placeholder="Suggested Operators"
                    :searchable="false" @input="(async function() {await _applyAddOpSuggestion(suggestion, $event)})()"
                    :clearable="false" class="formInputField"/>
        </div>

        <div v-if="suggestion instanceof AdjustParamAS">
          <ButtonSec class="applyButton" label="Apply Parameters" @click="suggestion.apply(operator);"/>
        </div>

      </div>
    </div>
  </div>
</template>

<script>

import CollapseHeader from "@/components/interface/elements/base/CollapseHeader.vue";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";
import {AddOpAS, AdjustParamAS} from "@/scripts/features/advisor/AdvisorSuggestion";
import ButtonSec from "@/components/interface/elements/base/ButtonSec.vue";

export default {
  components: {ButtonSec, CollapseHeader},
  props: {
    operator: {type: SvOperator, required: true},
  },

  computed: {
    AdjustParamAS() {
      return AdjustParamAS
    },

    AddOpAS() {
      return AddOpAS
    },

    suggestions() {
      return this.operator.advisorSuggestions;
    }
  },

  methods: {
    /** @param {AddOpAS} suggestion
     * @param {{name: String, path: String}} op */
    async _applyAddOpSuggestion(suggestion, op) {
      await suggestion.apply(op, this.operator);
    }
  }
}

</script>

<style scoped>

.sidebarAdvisor .v-select {
  width: 250px;
  margin: 5px auto 0;
}

.sidebarAdvisor {
  padding: 5px 0;
  border: 1px solid var(--warning-color);
  border-radius: 8px;
}

.sidebarAdvisorContent {
  padding: 0 10px 5px;
}

.sidebarAdvisor .applyButton {
  width: 250px;
  margin: 5px auto 0;

  border-color: var(--warning-color);
}

</style>

<style>

.sidebarAdvisor, .sidebarAdvisor .vs__selected {
  color: var(--warning-color) !important;
}

</style>
