<template>
  <div ref="plot" style="min-width:220px; min-height: 220px; width: 220px; height: 220px;"></div>
</template>

<script>
import Plotly from 'plotly.js-dist'
import BoolDS from "@/components/templates/displays/settings/BoolDS";
import StringDS from "@/components/templates/displays/settings/StringDS";
import RangeDS from "@/components/templates/displays/settings/RangeDS";
import {safeVal} from "@/scripts/tools/Utils";

export default {
  props: ['value', 'control'],

  data() {
    return {
      useXDif: false, //If the first element of the plot is the reference for all elements
      useYDif: false,

      useBuffer: false, //Stores incoming elements into a buffer and displays them together
      maxBufferElements: 0,
      bufferX: [],
      bufferY: []
    }
  },

  methods: {
    setValue(data) {
      this.value = data;

      if(data != null) {
        this._handlePlots(data.plots);
      } else Plotly.restyle(this.$refs.plot, {'y': [], 'x': []});
    },

    getSettingsOptions(props, propsDef) {
      //Expose some options to the user
      return [{"key": "xvisible", "name": "Show X Axis", "value": safeVal(props.xvisible, true), "desc": "Displays the x axis", "default": safeVal(propsDef.xvisible, true), "template": BoolDS},
        {"key": "yvisible", "name": "Show Y Axis", "value": safeVal(props.yvisible, true), "desc": "Displays the y axis", "default": safeVal(propsDef.yvisible, true), "template": BoolDS},
        {"key": "xtitle", "name": "X Title", "value": props.xtitle, "desc": "The title of the x axis", "default": propsDef.xtitle, "template": StringDS},
        {"key": "ytitle", "name": "Y Title", "value": props.ytitle, "desc": "The title of the y axis", "default": propsDef.ytitle, "template": StringDS},
        {"key": "xrange", "name": "X Range", "value": props.xrange, "desc": "The data range of the x axis", "default": propsDef.xrange, "template": RangeDS},
        {"key": "yrange", "name": "Y Range", "value": props.yrange, "desc": "The data range of the y axis", "default": propsDef.yrange, "template": RangeDS}];
    },

    _handlePlots(plots) {
      //if(data.length === 0) return;
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

        // Collect elements of this plot
        for (let i = 0; i < plot.length; i++) {
          let entry = plot[i];

          let xElement = 0
          let yElement = 0

          if (twoAxis) {
            if(this.useXDif) xElement = -(firstElement[0] - entry[0]);
            else xElement = entry[0];

            if(this.useYDif) yElement = -(firstElement[1] - entry[1]);
            else yElement = entry[1];
          } else {
            if(this.useBuffer) xElement = Date.now() // We need a constant increase in x, xDif not possible
            else xElement = x.length + 1;

            if(this.useYDif) yElement = -(firstElement - entry);
            else yElement = entry;
          }

          x.push(xElement);
          y.push(yElement);
        }

        xs.push(x);
        ys.push(y);

        // Update buffer with new values
        if(this.useBuffer) {
          // Verify max buffer elements
          if(x.length > this.maxBufferElements) {
            for(let i = 0; i < x.length - this.maxBufferElements; i++) {
              x.shift();
              y.shift();
            }
          }

          this.bufferX[p] = x;
          this.bufferY[p] = y;
        }
      }

      Plotly.restyle(this.$refs.plot, {'y': ys, 'x': xs});
    },

    setSettings(props) {
      // PLOTS

      if(props.plots !== undefined) {
        //Delete old traces
        while(this.$refs.plot.data.length>0) Plotly.deleteTraces(this.$refs.plot, 0);

        let p = [];

        for(let plot of props.plots) {
          p.push({
            x: [],
            y: [],
            type:"scatter",
            mode: safeVal(plot.mode, ""),
            hovertemplate: safeVal(plot.hover, "%{x:.2f}<br>%{y:.2f}<extra></extra>"),
            line: plot.line
          })
        }

        Plotly.addTraces(this.$refs.plot, p);
      }

      // LAYOUT

      let layout = {};

      this.useXDif = props.useXDif !== undefined ? props.useXDif : false;
      this.useYDif = props.useYDif !== undefined ? props.useYDif : false;

      this.useBuffer = props.useBuffer !== undefined ? props.useBuffer : false;
      this.maxBufferElements = props.maxBufferElements !== undefined ? props.maxBufferElements : 0;

      layout["xaxis.range"] = props.xrange !== undefined ? props.xrange : null;
      layout["yaxis.range"] = props.yrange !== undefined ? props.yrange : null;

      layout["xaxis.visible"] = props.xvisible !== undefined ? props.xvisible : true;
      layout["yaxis.visible"] = props.yvisible !== undefined ? props.yvisible : true;

      layout["xaxis.title.text"] = props.xtitle !== undefined ? props.xtitle : null;
      layout["yaxis.title.text"] = props.ytitle !== undefined ? props.ytitle : null;

      Plotly.relayout(this.$refs.plot, layout);
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

    onResize(entries) {
      let newW = 0;
      let newH = 0;

      entries.forEach(entry => {
        newW = entry.contentRect.width;
        newH = entry.contentRect.height;
      });

      Plotly.relayout(this.$refs.plot, {"width": newW, "height": newH, "autosize": true});
    },

    reset() {
      this.bufferX = [];
      this.bufferY = [];
    },
  },

  mounted() {
    Plotly.newPlot( this.$refs.plot, [{
      x: [],
      y: [],
      type:"scatter",
      mode:"", //Auto
      hovertemplate: "%{x:.2f}<br>%{y:.2f}<extra></extra>"
    }], this._getPlotConfig(), {displayModeBar: false});

    this.resizeObserver = new ResizeObserver(this.onResize);
    this.resizeObserver.observe(this.$el);
  },

  beforeDestroy() {
    this.resizeObserver.unobserve(this.$el);
  }
}
</script>

<style scoped>

</style>
