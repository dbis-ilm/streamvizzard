<template>
  <div>
    <div ref="plot"></div>
  </div>
</template>

<script>
import Plotly from 'plotly.js-dist'

export default {
  methods: {
    setStats: function(stats) {
      const x = [];
      const y = [];

      for (let v of stats) {
        x.push(v.timeStamp);
        y.push(v.exDuration);
      }

      Plotly.restyle(this.$refs.plot, {'y': [y], 'x': [x]});
    }
  },
  mounted() {
    Plotly.newPlot( this.$refs.plot, [{
      x: [],
      y: [],
      type:"scatter",
      hoverinfo: "y",
    }], {
      title: "Execution Time [ms]",
      width: 200,
      height: 200,
      hovermode:'closest',
      margin: {
        l: 25,
        r: 0,
        b: 5,
        t: 35,
        pad: 0
      },
      yaxis: {
        automargin: true,
        fixedrange: true
      },
      xaxis: {
        visible: false,
        fixedrange: true
      }
    }, {displayModeBar: false});
  }
}
</script>

<style scoped>

</style>
