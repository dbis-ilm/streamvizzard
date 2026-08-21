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
        let buffer = SvInstance.pipeline.getConnectionByID(this.modeSelected.conID).monitor.executionStats.entries;

        for(let b of buffer) {
          xData.push(b.time);
          yData.push(b.throughput);
        }
      } else if(this.modeSelected.type === "ExTime") {
        let buffer = this.operator.monitor.executionStats.entries;

        for(let b of buffer) {
          xData.push(b.time);
          yData.push(b.exTime);
        }
      } else if(this.modeSelected.type === "DataSize") {
        let buffer = this.operator.monitor.executionStats.entries;

        for(let b of buffer) {
          xData.push(b.time);
          yData.push(b.dataSize);
        }
      } else if(this.modeSelected.type === "DisplayTime") {
        let buffer = this.operator.monitor.executionStats.entries;

        let y2Data = [];

        for(let b of buffer) {
          let renderTime = b.displayRenderTime;

          if(renderTime === null) continue; // Only show entries with captured render time (some might be missed for high-frequency updates)

          xData.push(b.time);
          yData.push(b.displayFetchTime);
          y2Data.push(renderTime);
        }

        return {"x": xData, "y": [yData,y2Data]};
      }

      return {"x": xData, "y": [yData]};
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

    _onModeOptionsChanged(initial=false) {
      let options = [{"title": "Execution Time", "key": "ExecutionTime", "type": "ExTime"},
        {"title": "Output Data Size", "key": "DataSize", "type": "DataSize"}];

      for(const o of this.operator.outputs){
        for(let con of o.connections) {
          options.push({"title": "Throughput (Con. " + con.id + ")", "key": "Tp" + con.id, "type": "Tp", "conID": con.id});
        }
      }

      options.push({"title": "Display Time", "key": "DisplayTime", "type": "DisplayTime"});

      this.modeOptions = options;

      // First try to restore prev option (tentative - first type match)
      this.modeSelected = this.modeOptions.find(el => el.type === this.$streamvizzard.monitor.sideBarStatMode);

      // Fallback
      if(this.modeSelected == null) this.modeSelected = this.modeOptions.find(el => el.key === "ExecutionTime");

      this._onModeSelected(this.modeSelected, initial);
    },

    _onModeSelected(mode, force=false) {
      if(this.modeSelected === mode && !force) return;

      this.modeSelected = mode;
      this.$streamvizzard.monitor.sideBarStatMode = this.modeSelected.type;

      let yLabel = "";
      if(this.modeSelected.key === "ExecutionTime" || this.modeSelected.key === "DisplayTime") yLabel = "ms";
      else if(this.modeSelected.key === "DataSize") yLabel = "KB";
      else yLabel = "tup/s";

      let annotations = null;

      while(this.$refs.plot.data.length > 0) Plotly.deleteTraces(this.$refs.plot, 0);

      if(this.modeSelected.key === "DisplayTime") {
        Plotly.addTraces(this.$refs.plot, {
          type: 'scatter',
          name: 'Fetch',
          yaxis: {type: "linear"},
          xaxis: {type: "linear"},
          stackgroup: 'one'
        });

        Plotly.addTraces(this.$refs.plot, {
          type: 'scatter',
          name: 'Render',
          yaxis: {type: "linear"},
          xaxis: {type: "linear"},
          stackgroup: 'one'
        });

        annotations = [{
            text: "Fetch Data  <span style='color:blue'>━━━</span> ",
            x: 0,
            y: -0.235,
            xref: "paper",
            yref: "paper",
            xanchor: "left",
            showarrow: false
          }, {
            text: "<span style='color:orange'>━━━</span>  Render Data",
            x: 1,
            y: -0.235,
            xref: "paper",
            yref: "paper",
            xanchor: "right",
            showarrow: false
          }
        ];
      } else {
        Plotly.addTraces(this.$refs.plot, {
          type: 'scatter',
          mode: 'lines',
          name: 'trace0',
          yaxis: {type: "linear"},
          xaxis: {type: "linear"},
          stackgroup: 'one' // Adds fill to line
        });
      }

      Plotly.relayout(this.$refs.plot, {"yaxis.title.text": yLabel, "annotations": annotations});
      Plotly.restyle(this.$refs.plot, {"hovertemplate": "%{y:.2f} " + yLabel + "<extra></extra>"});
    },

    _plotData(xData, yData) {
      let deltaX = [];

      if(xData.length > 0) {
        let last = xData[xData.length - 1];

        for(let i = 0; i < xData.length; i++)
          deltaX.push((xData[i] - last));
      }

      Plotly.restyle(this.$refs.plot, {'y': yData, 'x': [deltaX], });
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
    Plotly.newPlot( this.$refs.plot, [], this._getPlotConfig(), {displayModeBar: false});

    this.resizeObserver = new ResizeObserver(() => Plotly.relayout(this.$refs.plot, {"autosize": true}));
    this.resizeObserver.observe(this.$el);

    registerEvent([EVENTS.CONNECTION_CREATED, EVENTS.CONNECTION_REMOVED], this._onConChanged);

    this._onModeOptionsChanged(true);
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
