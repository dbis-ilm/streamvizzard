<template>
  <div id="compilePipelineWindow" class="window" v-if="$streamvizzard.compiler.enabled">
    <div class="windowContent" :class="($streamvizzard.compiler.loading ? ' loading' : '')">
      <div class="windowTitle">Compile Pipeline <LoadingCircle v-if="$streamvizzard.compiler.loading" class="loadingCircle"/></div>

      <SwitchSelection v-model="optionsMode" :optionData="[
        {'value': 'placement', 'label': 'Placement'},
        {'value': 'compile', 'label': 'Compile'}]"/>

      <CompileStrategySelect v-show="optionsMode === 'placement'" class="optionSelect" ref="placementStrategySelect"
                             v-model="$streamvizzard.compiler.placementSettings" :strategyOptions="placementStrategyOptions"/>

      <CompileStrategySelect v-show="optionsMode === 'compile'" class="optionSelect" ref="compileStrategySelect"
                             v-model="$streamvizzard.compiler.compileSettings" :strategyOptions="compileStrategyOptions" :toggleSettings="false" :showStrategySelect="false"/>

      <div v-if="$streamvizzard.compiler.errorMessage != null" class="errorMsg" style="margin-top: 5px;" v-html="$streamvizzard.compiler.errorMessage"/>
      <div v-if="$streamvizzard.compiler.successMessage != null" class="successMsg" style="margin-top: 5px;" v-html="$streamvizzard.compiler.successMessage"/>

      <div class="modalFooterButtons">
        <ButtonSec :label="'Cancel'" @click="_triggerClose"/>
        <ButtonSec :class="!$streamvizzard.compiler.initialized ? 'disabled' : ''" :label="'Analyze'" @click="_triggerAnalyze">
          <i :class="['bi', 'bi-arrow-repeat', 'clickableIcon', 'autoAnalyzeToggle', $streamvizzard.compiler.autoAnalyze && 'activated']"
             title="Toggle automated re-analysis of the pipeline when compile targets were changed." @click="_toggleAutoAnalyze($event)"></i>
        </ButtonSec>
        <ButtonSec :label="'Compile'" :class="$streamvizzard.compiler.initialized && $streamvizzard.compiler.canCompile ? '' : 'disabled'" @click="_triggerCompile"/>
      </div>
    </div>
  </div>
</template>

<script>

//Future Work: We could also provide further heatmaps to view computeMode / language / parallelisms...

import ButtonSec from "@/components/interface/elements/base/ButtonSec.vue";
import CompileStrategySelect from "@/components/features/compiler/CompileStrategySelect.vue";
import SwitchSelection from "@/components/interface/elements/base/SwitchSelection.vue";
import {compileStrategies, placementStrategies} from "@/scripts/features/compiler/CompileStrategies";
import LoadingCircle from "@/components/interface/elements/base/LoadingCircle.vue";

export default {
  components: {LoadingCircle, SwitchSelection, CompileStrategySelect, ButtonSec},

  data() {
    return {
      optionsMode: "placement"
    }
  },

  computed: {
    placementStrategyOptions() {
      return placementStrategies;
    },

    compileStrategyOptions() {
      return compileStrategies;
    }
  },

  methods: {
    _triggerClose() {
      this.$streamvizzard.compiler.endCompileMode();
    },

    _triggerAnalyze() {
      this.$streamvizzard.compiler.analyzePipeline();
    },

    _triggerCompile() {
      this.$streamvizzard.compiler.compilePipeline();
    },

    _toggleAutoAnalyze(event) {
      event.stopPropagation();

      this.$streamvizzard.compiler.autoAnalyze = !this.$streamvizzard.compiler.autoAnalyze;
    }
  }
}
</script>

<style>

#compilePipelineWindow .compileGenResPath {
  font-style: italic;
  font-size: 0.75em;
  width: 100%;
  max-width: 100%;
}

</style>

<style scoped>

#compilePipelineWindow {
  position: absolute;
  left: 50%;
  transform: translate(-50%, 0);
  margin-top: -2px;
  border-top-left-radius: initial;
  border-top-right-radius: initial;
  width: 350px;
}

.optionSelect {
  margin-top: 10px;
}

.loading {
  pointer-events: none;
  opacity: 0.75;
}

.autoAnalyzeToggle {
  padding-left: 2px;
  cursor: pointer;
  opacity: 0.25;
}

.autoAnalyzeToggle.activated {
  opacity: 1;
}

.windowTitle {
  position: relative;
}

.loadingCircle {
  position: absolute;
  right: 0;
  top: 0;
}

</style>
