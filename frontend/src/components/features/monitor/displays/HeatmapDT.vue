<template>
  <ResizeElement :resizeKey="'DT'" :autoHide="true" :operator="operator" ref="plot" class="dtHeatmap"></ResizeElement>
</template>

<script>

import Plotly from 'plotly.js-dist'
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
    _applySettings(props) {
      let layout = {};

      layout["xaxis.title.text"] = props.xtitle;
      layout["yaxis.title.text"] = props.ytitle;

      layout["yaxis.range"] = props.yrange;

      Plotly.relayout(this.$refs.plot.$el, layout);

      Plotly.restyle(this.$refs.plot.$el, {"colorbar.title.text": props.ztitle});
    },

    _updateData(data) {
      if(data instanceof EmptyMonitorData) data = null;

      if(data != null) {
        Plotly.restyle(this.$refs.plot.$el, {'y': [data.y], 'x': [data.x], 'z': [data.z]});
      } else Plotly.restyle(this.$refs.plot.$el, {'y': null, 'x': null, 'z': null});
    },

    _getPlotConfig() {
      return {
        title: "",
        width: 210,
        height: 210,
        showlegend: false,
        hovermode: 'closest',
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
  },

  mounted() {
    Plotly.newPlot(this.$refs.plot.$el, [{
      x: [],
      y: [],
      z: [],
      type: "heatmap",
      colorscale: "Viridis"
    }], this._getPlotConfig(), {displayModeBar: false, dragMode: false, scrollZoom: false}).then((gd)=> {
      Plotly.relayout(gd, { autosize: true }); // Force initial layout

      if(this.$refs.plot) this._applySettings(this.settings);

      this.resizeObserver = new ResizeObserver(() => { // If we switch on load, this might return no plot
        if(this.$refs.plot) Plotly.relayout(this.$refs.plot.$el, {"autosize": true})
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

.dtHeatmap {
  min-width: 220px;
  min-height: 220px;
  width: 220px;
  height: 220px;
}

</style>

<style>

.dtHeatmap svg {
  border-radius: 2px;
  border: 1px solid var(--main-hover-color);
  box-sizing: border-box;
}

</style>
