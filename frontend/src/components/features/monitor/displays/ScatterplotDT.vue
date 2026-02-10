<template>
  <ResizeElement :resizeKey="'DT'" :autoHide="true" :operator="operator" ref="plot" class="dtPlot"></ResizeElement>
</template>

<script>

// Note: Plotly blocks pointermove events to allow interaction with the plot

import Plotly from 'plotly.js-dist'
import {safeVal} from "@/scripts/tools/Utils";
import ResizeElement from "@/components/pipeline/operator/ResizeElement.vue";

export default {
  components: {ResizeElement},
  props: {
    /** @type {SvOperator} */
    operator: {required: true},
    settings: {type: Object, required: true},
    value: {required: true},
  },

  data() {
    return {
      useXDif: false, //If the first element of the plot is the reference for all elements
      useYDif: false,

      useBuffer: false, //Stores incoming elements into a buffer and displays them together
      maxBufferElements: null,
      bufferX: [],
      bufferY: []
    }
  },

  watch: {
    value() {
      this._updateData(this.value);
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
        let plot = plots[p];

        let x = []
        let y = []

        // Load old buffer elements
        if(this.useBuffer) {
          if(this.bufferX.length - 1 >= p) x = this.bufferX[p];
          else this.bufferX.push([]);

          if(this.bufferY.length - 1 >= p) y = this.bufferY[p];
          else this.bufferY.push([]);
        }

        let twoAxis = Array.isArray(plot[0]);
        let firstElement = plot[plot.length - 1];

        let sampleRate = null;

        if(this.maxBufferElements != null && !this.useBuffer &&
            plot.length > this.maxBufferElements) {
          sampleRate = Math.ceil(plot.length / this.maxBufferElements);
        }

        // Collect elements of this plot
        for (let i = 0; i < plot.length; i++) {
          if(sampleRate != null && i % sampleRate !== 0) continue;

          let entry = plot[i];

          let xElement = 0
          let yElement = 0

          //TODO: Default xAxis label might be wrong (twoAxis with timestamp vs tupleCount)
          if (twoAxis) {
            if(this.useXDif) xElement = -(firstElement[0] - entry[0]);
            else xElement = entry[0];

            if(this.useYDif) yElement = -(firstElement[1] - entry[1]);
            else yElement = entry[1];
          } else {
            if(this.useBuffer) {
              xElement = time / 1000; // In Seconds

              // If the time value is smaller than the last one we remove all prev outdated values (occurs during traversal)

              for(let j = x.length - 1; j >= 0; j--) {
                let elm = x[j];

                if (xElement <= elm) x.pop();
                else break;
              }
            } else xElement = x.length + 1;

            if(this.useYDif) yElement = -(firstElement - entry);
            else yElement = entry;
          }

          x.push(xElement);
          y.push(yElement);
        }

        // Update buffer with new values & verify max buffer elements
        if(this.useBuffer) {
          if(this.maxBufferElements != null && x.length > this.maxBufferElements) {
            for(let i = 0; i < x.length - this.maxBufferElements; i++) {
              x.shift();
              y.shift();
            }
          }

          this.bufferX[p] = x;
          this.bufferY[p] = y;
        }

        xs.push(x);
        ys.push(y);
      }

      Plotly.restyle(this.$refs.plot.$el, {'y': ys, 'x': xs});
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
            type:"scatter",
            yaxis: {title: {text: "HI"}},
            mode: safeVal(plot.mode, ""),
            hovertemplate: safeVal(plot.hover, "%{x:.2f}<br>%{y:.2f}<extra></extra>"),
            line: plot.line
          })
        }

        Plotly.addTraces(this.$refs.plot.$el, p);
      }

      // LAYOUT

      let layout = {};

      this.useXDif = props.useXDif != null ? props.useXDif : this.useXDif;
      this.useYDif = props.useYDif != null ? props.useYDif : this.useXDif;

      this.useBuffer = props.useBuffer != null ? props.useBuffer : this.useBuffer;
      this.maxBufferElements = props.maxBufferElements != null ? parseInt(props.maxBufferElements) : this.maxBufferElements;

      layout["xaxis.range"] = props.xrange;
      layout["yaxis.range"] = props.yrange;

      layout["xaxis.visible"] = props.xvisible;
      layout["yaxis.visible"] = props.yvisible;

      layout["xaxis.title.text"] = props.xtitle;
      layout["yaxis.title.text"] = props.ytitle;

      Plotly.relayout(this.$refs.plot.$el, layout);
    },

    _updateData(data) {
      // In case of buffer not all elements might be transmitted during debug traversal due to message transfer optimization

      if(data != null) {
        this._handlePlots(data.plots, data.time);
      } else {
        this.bufferX = [];
        this.bufferY = [];

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
          visible: true
        },
        xaxis: {
          visible: true,
          fixedrange: true,
          automargin: true
        }
      };
    },

    reset() {
      this.bufferX = [];
      this.bufferY = [];
    },
  },

  mounted() {
    Plotly.newPlot( this.$refs.plot.$el, [{
      x: [],
      y: [],
      type:"scatter",
      mode:"", //Auto
      hovertemplate: "%{x:.2f}<br>%{y:.2f}<extra></extra>"
    }], this._getPlotConfig(), {displayModeBar: false, dragMode: false, scrollZoom: false}).then((gd)=> {
      Plotly.relayout(gd, { autosize: true }); // Force initial layout

      this.resizeObserver = new ResizeObserver(() => Plotly.relayout(this.$refs.plot.$el, {"autosize": true}));
      this.resizeObserver.observe(this.$el);
    });

    this._applySettings(this.settings);
  },

  beforeDestroy() {
    this.resizeObserver.unobserve(this.$el);
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
