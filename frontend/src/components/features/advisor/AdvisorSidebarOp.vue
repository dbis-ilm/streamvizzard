<template>
  <div v-if="suggestions != null" class="sidebarAdvisor">
    <CollapseHeader :openedDir="'up'" class="sectionHeader" v-model="$streamvizzard.advisor.showSidebar" title="Advisions"/>
    <div class="sidebarAdvisorContent" v-show="$streamvizzard.advisor.showSidebar">
      <div v-for="(suggestion, index) in suggestions" :key="suggestion.key"
           style="margin-top: 10px;">
        <div><b>{{ index + 1 }})</b> {{ suggestion.msg }}</div>
        <div v-if="suggestion.ops != null">
          <v-select v-auto-blur :options="suggestion.ops" label="name" placeholder="Suggested Operators"
                    :searchable="false" @input="(async function() {await _onAdvisorOperatorSelect($event)})()"
                    :clearable="false"></v-select>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import CollapseHeader from "@/components/interface/elements/base/CollapseHeader.vue";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";

export default {
  components: {CollapseHeader},
  props: {
    operator: {type: SvOperator, required: true},
  },

  computed: {
    suggestions() {
      return this.operator.advisorSuggestions;
    }
  },

  methods: {
    async _onAdvisorOperatorSelect(event) {
      // Find selected operator by path

      let def = this.$streamvizzard.modules.getOperatorDefinition(event.path);

      if(def == null) return;

      // Instantiate operator

      let op = await this.$streamvizzard.pipeline.createOperator(def, {x: this.operator.posX - 60, y: this.operator.posY + 60});

      if(op != null) this.$streamvizzard.editor.selectOperator(op);
    },
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

</style>

<style>

.sidebarAdvisor, .sidebarAdvisor .vs__selected {
  color: var(--warning-color) !important;
}

</style>
