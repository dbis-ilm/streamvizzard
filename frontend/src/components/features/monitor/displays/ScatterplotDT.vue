<template>
  <ResizeElement :resizeKey="'DT'" :autoHide="true" :operator="operator" ref="plot" class="dtPlot"></ResizeElement>
</template>

<script>

// Note: Plotly blocks pointermove events to allow interaction with the plot
// Multi-plots need respective settings configuration to set up traces!
// For non-buffer modes: The plot may contain two axis if providing an additional x component [occurs for sampled data]

import Plotly from 'plotly.js-dist'
import {safeVal} from "@/scripts/tools/Utils";
import ResizeElement from "@/components/pipeline/operator/ResizeElement.vue";
import {EmptyMonitorData} from "@/scripts/features/monitor/OperatorMonitor";

export default {
  components: {ResizeElement},
  inject: ['performTrackedRender'],
  props: {
    /** @type {SvOperator} */
    operator: {required: true},
    settings: {type: Object, required: true},
    value: {required: true}
  },

  data() {
    return {
      useBuffer: false, // Stores incoming elements into a buffer and displays them together
      maxBufferElements: null,
      bufferX: [],
      bufferY: [],
      lastTime: null
    }
  },

  watch: {
    value() {
      this.performTrackedRender(() => { this._updateData(this.value) });
    },

    settings: {
      handler() {
        this._applySettings(this.settings);
        this._updateData(this.value);
      }, deep: true
    }
  },

  methods: {
    _handlePlots(plots, time) {
      let xs = [];
      let ys = [];

      // Handle all plots
      for (let p in plots) {
        let plotData = plots[p];

        let plotX = []
        let plotY = []

        // Load old buffer elements
        if(this.useBuffer) {
          if(this.bufferX.length - 1 >= p) plotX = this.bufferX[p];
          else this.bufferX.push([]);

          if(this.bufferY.length - 1 >= p) plotY = this.bufferY[p];
          else this.bufferY.push([]);
        }

        // Collect elements of this plot
        for (let i = 0; i < plotData.length; i++) {
          let data = plotData[i];

          // Determine x value

          let xElement;
          let yElement;

          // Use delta time
          if(this.useBuffer) {
            yElement = data;
            xElement = time // Time=Seconds

            // If the time value is smaller than the last one we remove all prev outdated values (occurs during traversal)
            // Low effort solution which is unreliable for branch switches (forward movement in different branch), this is fine for now

            for(let j = plotX.length - 1; j >= 0; j--) {
              let prevElm = plotX[j];

              if (prevElm >= xElement) {
                plotX.pop();
                plotY.pop();
              } else break;
            }
          }

          else { // Non-buffer plots may provide an additional x-axis component
            if(Array.isArray(data)) {
              yElement = data[1];
              xElement = data[0];
            } else {
              yElement = data;
              xElement = plotX.length + 1;  // Use tuple number
            }
          }

          plotX.push(xElement);
          plotY.push(yElement);
        }

        // Update buffer with new values & verify max buffer elements

        if(this.useBuffer) {
          if(this.maxBufferElements != null && plotX.length >= this.maxBufferElements) {
            for(let i = 0; i < plotX.length - this.maxBufferElements; i++) {
              plotX.shift();
              plotY.shift();
            }
          }

          this.bufferX[p] = plotX;
          this.bufferY[p] = plotY;

          // Apply delta-Time calculation to the x-data (without affecting stored buffer content)

          let lastElm = plotX[plotX.length - 1];
          plotX = plotX.map((x) => x - lastElm);
        }

        xs.push(plotX);
        ys.push(plotY);
      }

      this.lastTime = time;

      Plotly.restyle(this.$refs.plot.$el, {y: ys, x: xs});
    },

    _applySettings(props) {
      // PLOTS

      if(props.plots != null) {
        //Delete old traces
        while(this.$refs.plot.$el.data.length>0) Plotly.deleteTraces(this.$refs.plot.$el, 0);

        let p = [];

        for(let plot of props.plots) {
          p.push({
            x: [],
            y: [],
            type: "scatter",
            yaxis: {type: "linear"},
            xaxis: {type: "linear"},
            mode: safeVal(plot.mode, ""),
            hovertemplate: safeVal(plot.hover, "%{x:.2f}<br>%{y:.2f}<extra></extra>"),
            line: plot.line
          })
        }

        Plotly.addTraces(this.$refs.plot.$el, p);
      }

      // LAYOUT

      let layout = {};

      this.useBuffer = props.useBuffer != null ? props.useBuffer : this.useBuffer;
      this.maxBufferElements = props.maxBufferElements != null ? parseInt(props.maxBufferElements) : this.maxBufferElements;

      // Either both sides or none can be set. If only one is set, Plotly defaults to auto-range.
      // Problem: one-sided range is invalidated by data update. Performing this after data update might lead
      // to invalid ranges (if data is smaller than min range) which will again default to auto-range.
      // Only stable solution would be to manually track min/max sides, which is quite a lot of manual effort.

      layout["yaxis.range"] = props.yrange;
      layout["xaxis.range"] = props.xrange;

      layout["xaxis.visible"] = props.xvisible;
      layout["yaxis.visible"] = props.yvisible;

      layout["xaxis.title.text"] = props.xtitle;
      layout["yaxis.title.text"] = props.ytitle;

      Plotly.relayout(this.$refs.plot.$el, layout);
    },

    _updateData(data) {
      // Note: In case of buffer not all elements might be transmitted during debug traversal due to message transfer optimization

      // If we receive "missing data", artificially add null values for each previous plot inside the data buffer
      // Add small offset the last time to avoid eviction of "outdated" data
      // For non-buffer displays, we clear the plot since no data was transmitted

      if(data instanceof EmptyMonitorData) {
        if(this.useBuffer) data = { "plots": this.bufferX.map(() => [null]), "time": this.lastTime + 1e-6 };
        else data = null;
      }

      if(data != null) this._handlePlots(data.plots, data.time);
      else {
        this.bufferX = [];
        this.bufferY = [];
        this.lastTime = null;

        Plotly.restyle(this.$refs.plot.$el, {'y': null, 'x': null});
      }
    },

    _getPlotConfig() {
      return {
        title: "",
        width: 210,
        height: 210,
        showlegend: false,
        hovermode:'closest',
        margin: {
          l: 5,
          r: 5,
          b: 5,
          t: 5,
          pad: 0
        },
        yaxis: {
          automargin: true,
          fixedrange: true,
          visible: true,
          type: "linear"
        },
        xaxis: {
          visible: true,
          fixedrange: true,
          automargin: true,
          type: "linear"
        }
      };
    },

    reset() {
      this.bufferX = [];
      this.bufferY = [];
    },
  },

  mounted() {
    Plotly.newPlot(this.$refs.plot.$el, [{
      x: [],
      y: [],
      type: "scatter",
      mode: "lines",
      yaxis: {type: "linear"},
      xaxis: {type: "linear"},
      hovertemplate: "%{x:.2f}<br>%{y:.2f}<extra></extra>"
    }], this._getPlotConfig(), {displayModeBar: false, dragMode: false, scrollZoom: false}).then((gd)=> {
      Plotly.relayout(gd, { autosize: true }); // Force initial layout

      if(this.$refs.plot) this._applySettings(this.settings);

      this.resizeObserver = new ResizeObserver(() => { // If we switch on load, this might return no plot
        if(this.$refs.plot) Plotly.relayout(this.$refs.plot.$el, {"autosize": true});
      });

      this.resizeObserver.observe(this.$el);
    });
  },

  beforeDestroy() {
    this.resizeObserver?.unobserve(this.$el);
  }
}
</script>

<style scoped>

.dtPlot {
  min-width:220px;
  min-height: 220px;
  width: 220px;
  height: 220px;
}

</style>

<style>

.dtPlot svg {
  border-radius: 2px;
  border: 1px solid var(--main-hover-color);
  box-sizing: border-box;
}

</style>
