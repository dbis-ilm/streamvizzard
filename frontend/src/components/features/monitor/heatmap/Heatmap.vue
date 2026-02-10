<template>
  <div class="heatmapContainer">
    <div id="heatmapStats" class="heatmapComponent" v-if="hmType > 1">
      <div style="text-align: left;"><b>Operator Heatmap</b></div>
      <div style="text-align:left; margin-top:10px;">{{title}}</div>
      <div class="heatmapGradient" ref="gradient">
        <div class="heatmapLegendMark" style="top:-0.2em; left:48px;">{{minVal}}</div>
        <div class="heatmapLegendMark" style="bottom:-0.2em; left:48px;">{{maxVal}}</div>
        <div ref="heatmapLegendSteps" id="heatmapLegendSteps" style="left:48px;">
          <div class="hmLegendStep" v-for="step in stepData" :key="step['id']" v-show="step['visible']"
               :style="'position:absolute; top: calc(' + step['pos'] + 'px - 0.5em)'">{{ step["val"] }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {HEATMAP} from "@/scripts/features/monitor/Monitor";

export default {
  props: {
    hmType: {type: Number, required: true},
  },

  data() {
    return {
      minVal: "0",
      maxVal: "0",

      stepData: [],
    }
  },

  computed: {
    heatmapData() {
      return this.$streamvizzard.monitor.heatmapData;
    },

    title() {
      if(this.hmType === HEATMAP.DATA_SIZE) {
        return "Data Size (KB)";
      } else if(this.hmType === HEATMAP.EXECUTION_TIME) {
        return "Execution Time (ms)";
      }

      return "";
    }
  },

  watch: {
    heatmapData() {
      let data = this.heatmapData;

      if(data != null) this.onDataUpdate(data["min"], data["max"], data["steps"]);
      else this.onDataUpdate(0, 0, []);
    }
  },

  methods: {
    onDataUpdate(min, max, steps) {
      this.minVal = min.toFixed(2);
      this.maxVal = max.toFixed(2);

      let gradientHeight = this.$refs.gradient.clientHeight;

      let currentStepCount = this.stepData.length;

      if(currentStepCount !== steps.length) {
        this.stepData = [];
      }

      for(let i=0; i < steps.length; i++)  {
        let step = steps[i];
        let stepRelVal = step[1];

        let stepVal = step[0].toFixed(2);
        let stepPos = Math.round(gradientHeight * step[1]);
        let stepVisible = true;

        if(i === 0 && stepVal === this.minVal) stepVisible = false;  // If it's the first step and has the same as the min value
        else if(stepRelVal > 0.875 || stepRelVal <= 0.1) stepVisible = false; // If it's to close to the min/max border

        let data = {"id": i, "pos": stepPos, "val": stepVal, "visible": stepVisible};

        if(i < currentStepCount) this.stepData[i] = data;
        else this.stepData.push(data);
      }
    }
  },
}

</script>

<style scoped>

.heatmapContainer {
  position:absolute;
  top:-2px;
  left: 14px;
  padding: 0 4px;
  background: white;
  border: 2px solid var(--main-border-color);
  border-radius: var(--window-border-radius);
}

.heatmapLegendMark, #heatmapLegendSteps {
  text-align:left;
  white-space: nowrap;
  position: absolute;
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
