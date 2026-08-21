<template>
  <div class="heatmapContainer" :style="'left: ' + ($streamvizzard.interface.opPresetBarViewRect.right - 2) + 'px'">
    <div id="heatmapStats" class="heatmapComponent" v-if="$streamvizzard.monitor.heatmap.isExStats()">
      <div style="text-align: left;"><b>Operator Heatmap</b></div>
      <v-select v-auto-blur :clearable="false" :searchable="false" :options="modeOptions" class="formInputField modeOptions"
                :reduce="mode => mode.key" :value="$streamvizzard.monitor.heatmap.type" @input="_onModeSelected($event)"/>
      <div class="heatmapGradient" ref="gradient">
        <div class="heatmapUnit">{{title}}</div>
        <div class="heatmapLegendMark" style="top:-0.2em; left:48px;">{{$streamvizzard.monitor.heatmap.min.toFixed(2)}}</div>
        <div class="heatmapLegendMark" style="bottom:-0.2em; left:48px;">{{$streamvizzard.monitor.heatmap.max.toFixed(2)}}</div>
        <div ref="heatmapLegendSteps" id="heatmapLegendSteps" style="left:48px;">
          <div class="hmLegendStep" v-for="step in stepData" :key="step['id']" v-show="step['visible']"
               :style="'position:absolute; top: calc(' + step['pos'] + 'px - 0.5em)'">{{ step["val"] }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import {HEATMAP} from "@/scripts/features/monitor/Heatmap";

export default {
  data() {
    return {
      stepData: [],
      modeOptions: [
        {"key": HEATMAP.EXECUTION_TIME, "label": "Execution Time"},
        {"key": HEATMAP.DATA_SIZE, "label": "Output Size"},
        {"key": HEATMAP.THROUGHPUT, "label": "Throughput"},
        {"key": HEATMAP.DISPLAY_FETCH_TIME, "label": "Display Fetch"},
        {"key": HEATMAP.DISPLAY_RENDER_TIME, "label": "Display Render"}
      ]
    }
  },

  computed: {
    heatmapSteps() {
      return this.$streamvizzard.monitor.heatmap.steps;
    },

    title() {
      if(this.$streamvizzard.monitor.heatmap.type === HEATMAP.DATA_SIZE) {
        return "(KB)";
      } else if(this.$streamvizzard.monitor.heatmap.type === HEATMAP.EXECUTION_TIME) {
        return "(ms)";
      } else if(this.$streamvizzard.monitor.heatmap.type === HEATMAP.THROUGHPUT) {
        return "(tup/s)";
      } else if(this.$streamvizzard.monitor.heatmap.type === HEATMAP.DISPLAY_FETCH_TIME) {
        return "(ms)";
      } else if(this.$streamvizzard.monitor.heatmap.type === HEATMAP.DISPLAY_RENDER_TIME) {
        return "(ms)";
      }

      return "";
    }
  },

  watch: {
    heatmapSteps() {
      let gradientHeight = this.$refs.gradient.clientHeight;

      let currentStepCount = this.stepData.length;

      if(currentStepCount !== this.heatmapSteps.length) this.stepData = [];

      for(let i=0; i < this.heatmapSteps.length; i++)  {
        let step = this.heatmapSteps[i];
        let stepRelVal = step[1];

        let stepVal = step[0].toFixed(2);
        let stepPos = Math.round(gradientHeight * step[1]);
        let stepVisible = true;

        if(i === 0 && step[0] === this.$streamvizzard.monitor.heatmap.min) stepVisible = false;  // If it's the first step and has the same as the min value
        else if(stepRelVal > 0.875 || stepRelVal <= 0.1) stepVisible = false; // If it's to close to the min/max border

        let data = {"id": i, "pos": stepPos, "val": stepVal, "visible": stepVisible};

        if(i < currentStepCount) this.stepData[i] = data;
        else this.stepData.push(data);
      }
    },
  },

  methods: {
    _onModeSelected(hmType) {
      this.$streamvizzard.monitor.heatmap.show(hmType);
    }
  }
}

</script>

<style scoped>

.heatmapContainer {
  min-width: 150px;
  position:absolute;
  top: -2px;
  padding: 2px 8px;
  background: white;
  border: 2px solid var(--main-border-color);
  border-radius: var(--window-border-radius);
  cursor: default;
}

.heatmapContainer .modeOptions {
  padding-top: 5px;
  margin-bottom: 30px;
}

.heatmapLegendMark, #heatmapLegendSteps {
  text-align:left;
  white-space: nowrap;
  position: absolute;
}

.heatmapContainer .heatmapUnit {
  text-align: center;
  position: absolute;
  top: -25px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
}

.heatmapGradient {
  position: relative;
  margin: 5px 10px 5px 10px;
  height:200px;
  width: 40px;

  background: linear-gradient(180deg, rgba(0,200,255,1) 0%, rgba(255,255,100,1) 33%, rgba(255,100,100,1) 66%, rgba(255,100,255,1) 100%);
  border-radius: var(--window-border-radius);
  border: 1px solid var(--main-border-color);
}

</style>
