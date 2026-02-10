<template>
  <div ref="element" class="heatmapOp" :style="'box-shadow: 0px 0px 125px 75px '
    + heatmapColor + '; transform:translate(' + operator.posX + 'px, ' + operator.posY + 'px);' +
     'width: ' + operator.width + 'px; height: ' + operator.height + 'px; z-index:' + Math.round(operator.monitor.heatmapRating * 100) + ';'"></div>
</template>

<script>
import {clamp} from "@/scripts/tools/Utils";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";
import $ from "jquery";

export default {
  props: {
    operator: {type: SvOperator, required: true},
  },

  methods: {
    _calcHeatmapColor(gradientValue) {
      gradientValue = clamp(gradientValue, 0, 1);

      const sliderWidth = 1

      const gradient = [
        [
          0,
          [100, 200, 255]
        ],
        [
          0.33,
          [255, 255, 100]
        ],
        [
          0.66,
          [255, 100, 100]
        ],
        [
          1,
          [255, 100, 255]
        ]
      ];

      if (gradientValue === 0) return 'rgb(' + gradient[0][1][0] + ',' + gradient[0][1][1] + ',' + gradient[0][1][2] + ')';
      else if (gradientValue === 1) return 'rgb(' + gradient[gradient.length - 1][1][0] + ',' + gradient[gradient.length - 1][1][1] + ',' + gradient[gradient.length - 1][1][2] + ')';

      let colorRange = []
      $.each(gradient, function (index, value) {
        if (gradientValue <= value[0]) {
          colorRange = [Math.max(0, index - 1), index]
          return false;
        }
      });

      //Get the two closest colors
      let firstCol = gradient[colorRange[0]][1];
      let secondCol = gradient[colorRange[1]][1];

      //Calculate ratio between the two closest colors
      let firstColX = sliderWidth * (gradient[colorRange[0]][0]);
      let secondColX = sliderWidth * (gradient[colorRange[1]][0]) - firstColX;
      let sliderX = sliderWidth * (gradientValue) - firstColX;
      let ratio = sliderX / secondColX;

      //Get the color with pickHex(thx, less.js's mix function!)
      let result = this._pickHex(secondCol, firstCol, ratio);

      return 'rgb(' + result[0] + ',' + result[1] + ',' + result[2] + ')';
    },

    _pickHex(color1, color2, weight) {
      let w = weight * 2 - 1;
      let w1 = (w + 1) / 2;
      let w2 = 1 - w1;
      return [Math.round(color1[0] * w1 + color2[0] * w2),
        Math.round(color1[1] * w1 + color2[1] * w2),
        Math.round(color1[2] * w1 + color2[2] * w2)];
    }
  },

  computed: {
    heatmapColor() {
      return this._calcHeatmapColor(this.operator.monitor.heatmapRating);
    }
  }
}
</script>

<style scoped>

.heatmapOp {
  width: 200px;
  height: 200px;
  pointer-events: none;
  border-radius: var(--node-border-radius);
  transform-origin: center;
}

</style>
