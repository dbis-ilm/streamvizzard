<template>
  <div class="container">
    <div class="title">Execution Statistics</div>
    <div class="formInputContainer">
      <span class="formInputLabel limitedText alignLeft">Statistics:&nbsp;</span>
      <v-select v-auto-blur :clearable="false" :searchable="false" :options="modeOptions" class="formInputField modeOptions" :value="modeSelected" @input="_onModeSelected($event)" label="title"></v-select>
    </div>

    <div ref="plot" class="exPlot"></div>
  </div>
</template>

<script>
import Plotly from 'plotly.js-dist'
import {EVENTS, registerEvent, unregisterEvent} from "@/scripts/tools/EventHandler";
import {SvInstance} from "@/scripts/StreamVizzard";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";

export default {
  name: "ExecutionStatsPlot",
  props: {
    operator: {type: SvOperator, required: true},
  },

  data() {
    return {
      modeOptions: [],
      modeSelected: null,
    }
  },

  computed: {
    data() {
      let xData = [];
      let yData = [];

      if(this.modeSelected == null) return {"x": xData, "y": yData};

      if(this.modeSelected.type === "Tp") {
        let buffer = SvInstance.pipeline.getConnectionByID(this.modeSelected.conID).monitor.tpBuffer;

        for(let b of buffer) {
          xData.push(b["time"]);
          yData.push(b["tp"]);
        }
      } else if(this.modeSelected.type === "ExTime") {
        let buffer = this.operator.monitor.statsBuffer;

        for(let b of buffer) {
          xData.push(b["time"]);
          yData.push(b["exTime"]);
        }
      } else if(this.modeSelected.type === "DataSize") {
        let buffer = this.operator.monitor.statsBuffer;

        for(let b of buffer) {
          xData.push(b["time"]);
          yData.push(b["dataSize"] / 1000); // Server sends bytes -> show KB
        }
      }

      return {"x": xData, "y": yData};
    }
  },

  watch: {
    operator() {
      this._onModeOptionsChanged();
    },

    data() {
      let data = this.data;
      this._plotData(data["x"], data["y"]);
    },
  },

  methods: {
    /** @param {SvConnection} con **/
    _onConChanged(con) {
      if(con.input.operator === this.operator || con.output.operator === this.operator)
        this._onModeOptionsChanged();
    },

    _onModeOptionsChanged() {
      let options = [{"title": "Execution Time", "key": "ExecutionTime", "type": "ExTime"},
        {"title": "Data Size", "key": "DataSize", "type": "DataSize"}];

      for(const o of this.operator.outputs){
        for(let con of o.connections) {
          options.push({"title": "Throughput (Con. " + con.id + ")", "key": "Tp" + con.id, "type": "Tp", "conID": con.id});
        }
      }

      this.modeOptions = options;

      // First try to restore prev option (tentative - first type match)
      this.modeSelected = this.modeOptions.find(el => el.type === this.$streamvizzard.monitor.sideBarStatMode);

      // Fallback
      if(this.modeSelected == null) this.modeSelected = this.modeOptions.find(el => el.key === "ExecutionTime");

      this._onModeSelected(this.modeSelected);
    },

    _onModeSelected(mode) {
      this.modeSelected = mode;
      this.$streamvizzard.monitor.sideBarStatMode = this.modeSelected.type;

      let yLabel = "";
      if(this.modeSelected.key === "ExecutionTime") yLabel = "ms";
      else if(this.modeSelected.key === "DataSize") yLabel = "KB";
      else yLabel = "tup/s";

      Plotly.relayout(this.$refs.plot, {"yaxis.title.text": yLabel});
      Plotly.restyle(this.$refs.plot, {"hovertemplate": "%{y:.2f} " + yLabel + "<extra></extra>"});
    },

    _plotData(xData, yData) {
      let deltaX = [];

      if(xData.length > 0) {
        let last = xData[xData.length - 1];

        for(let i = 0; i < xData.length; i++)
          deltaX.push((xData[i] - last));
      }

      Plotly.restyle(this.$refs.plot, {'y': [yData], 'x': [deltaX], });
    },

    _getPlotConfig() {
      return {
        title: "",
        showlegend: false,
        hovermode:'closest',
        margin: {
          l: 5,
          r: 5,
          b: 5,
          t: 5,
          pad: 5
        },
        yaxis: {
          automargin: true,
          fixedrange: true,
          visible: true,
          title: {text: "ms", standoff: 5},
          side: "right"
        },
        xaxis: {
          visible: true,
          fixedrange: true,
          automargin: true,
          title: {text: "Δs"}
        }
      };
    },
  },

  mounted() {
    Plotly.newPlot( this.$refs.plot, [{
      x: [],
      y: [],
      type:"scatter",
      mode:"", //Auto
      hovertemplate: "%{y:.2f}<extra></extra>",
    }], this._getPlotConfig(), {displayModeBar: false});

    this.resizeObserver = new ResizeObserver(() => Plotly.relayout(this.$refs.plot, {"autosize": true}));
    this.resizeObserver.observe(this.$el);

    registerEvent([EVENTS.CONNECTION_CREATED, EVENTS.CONNECTION_REMOVED], this._onConChanged);

    this._onModeOptionsChanged();
  },

  beforeDestroy() {
    this.resizeObserver.unobserve(this.$el);

    unregisterEvent([EVENTS.CONNECTION_CREATED, EVENTS.CONNECTION_REMOVED], this._onConChanged);
  }
}
</script>

<style scoped>

.title {
  text-decoration: underline;
}

.exPlot {
  width: 100%;
  height: 220px;
  margin-top: 12px;
}

.modeOptions {
  margin-left: 10px;
}

</style>

<style>

.exPlot svg {
  border-radius: 2px;
  border: 1px solid var(--second-border-color);
  box-sizing: border-box;
}

</style>
