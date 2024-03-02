<template>
<div class="canvas">
  <canvas ref="bgCanvas" class="mouseEventBlocker" :width="width" :height="height" style="z-index: 1;"></canvas>
  <canvas ref="fgCanvas" class="mouseEventBlocker" :width="width" :height="height" style="z-index: 2;"></canvas>
</div>
</template>

<script>
//TODO: OPTIMIZE WITH OFFSCREENCANVAS & WEBWORKER?

export default {
  name: "CanvasDT",

  data() {
    return {
      width: 1000,
      height: 1000,
      lines: [],
      bgImg: null,

      offscreenCanvas: null
    }
  },

  methods: {
    setValue(data) {
      if(data == null) return;

      if(this.width !== data.size[0]) {
        this.width = data.size[0];
        this.offscreenCanvas.width = this.width;
      }

      if(this.height !== data.size[1]) {
        this.height = data.size[1];
        this.offscreenCanvas.height = this.height;
      }

      this.lines = data.lines;

      if(this.bgImg === null) { // TODO: ONLY WHEN CHANGED?
        this.bgImg = new Image();
        this.bgImg.onload = this.updateBG;
      }

      if(data.updateImg) this.bgImg.src = 'data:image/png;base64,' + data.bgImg;

      // let start = performance.now();
      requestAnimationFrame(this.updateFG);
      // let end = performance.now();

      // console.log("Rendering took: " + (end - start) + " ms!");
    },

    updateBG() {
      let canvas = this.$refs.bgCanvas;
      let ctx = canvas.getContext("2d")

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw Background

      ctx.drawImage(this.bgImg, 0, 0);
    },

    updateFG() {
      //let fgCanvas = this.$refs.fgCanvas;
      //let fgCtx = fgCanvas.getContext("2d")
      let fgCanvas = this.offscreenCanvas;
      let fgCtx = this.offscreenCanvas.getContext("2d");

      //Clear Canvas

      fgCtx.clearRect(0, 0, fgCanvas.width, fgCanvas.height);

      // Draw Lines

      //fgCtx.beginPath();

      // let totalPoints = 0;
      for(let line of this.lines) {
        let points = line.points;
        let color = line.color;
        let width = line.width;

        if(color.length === 4) fgCtx.strokeStyle = 'rgba(' + color[0] + ',' + color[1] + ',' + color[2] + ',' + (color[3] / 255.0) + ')';
        else if(color.length === 3) fgCtx.strokeStyle = 'rgb(' + color[0] + ',' + color[1] + ',' + color[2] + ')';

        fgCtx.lineWidth = width;
        fgCtx.lineCap = 'round' //TODO: SETTINGS?

        fgCtx.beginPath();

        let lastPoint = null;

        for(let point of points) {
          if(point != null) { //Null to separate path into segments
            // totalPoints += 1;

            if(lastPoint != null) fgCtx.lineTo(point[0], point[1]);

            fgCtx.moveTo(point[0], point[1]);
          }

          lastPoint = point;
        }

        let start = performance.now();
        fgCtx.stroke();
        let end = performance.now();
        if(end - start > 5) console.log("Draw Line (" + points + " points) took: " + (end - start) + " ms!");
      }

      //fgCtx.stroke();

      let mainCtx = this.$refs.fgCanvas.getContext("2d");
      mainCtx.clearRect(0, 0, fgCanvas.width, fgCanvas.height);
      mainCtx.drawImage(fgCanvas, 0, 0);

      // console.log("TOTAL POINTS: " + totalPoints + ", LINES: " + this.lines.length);
    },

    tes() {
      let fgCanvas = this.offscreenCanvas;
      let dynCtx = this.offscreenCanvas.getContext("2d");

      // let start = performance.now();

      dynCtx.clearRect(0, 0, fgCanvas.width, fgCanvas.height);

      dynCtx.lineWidth = 5;
      dynCtx.lineCap = 'round';
      dynCtx.strokeStyle = 'rgba(255, 0, 0, 0.2)';

      //dynCtx.beginPath();

      for(let i = 0; i < 1000; i++) {
        let x1 = Math.floor(Math.random() * (this.width));
        let y1 = Math.floor(Math.random() * (this.height));

        let x2 = Math.floor(Math.random() * (this.width));
        let y2 = Math.floor(Math.random() * (this.height));

        let x3 = Math.floor(Math.random() * (this.width));
        let y3 = Math.floor(Math.random() * (this.height));

        dynCtx.beginPath();
        dynCtx.moveTo(x1, y1);
        dynCtx.lineTo(x2, y2);
        dynCtx.moveTo(x2, y2);
        dynCtx.lineTo(x3, y3);

        dynCtx.stroke();
      }

      let mainCanvas = this.$refs.fgCanvas;
      let mainCtx = mainCanvas.getContext("2d")
      mainCtx.clearRect(0, 0, fgCanvas.width, fgCanvas.height);
      mainCtx.drawImage(fgCanvas, 0, 0);

      //dynCtx.stroke();  //Speedup if we draw stroke in the end, but we loose transparency!

      // let end = performance.now();

      // console.log("Rendering took: " + (end - start) + " ms!");
    },

    reset() {
      this.$refs.fgCanvas.getContext("2d").clearRect(0, 0,  this.$refs.fgCanvas.width,  this.$refs.fgCanvas.height);
      this.$refs.bgCanvas.getContext("2d").clearRect(0, 0,  this.$refs.bgCanvas.width,  this.$refs.bgCanvas.height);
    }
  },

  mounted() {
    this.offscreenCanvas = document.createElement('canvas');
    this.offscreenCanvas.width = this.width;
    this.offscreenCanvas.height = this.height;

    //this.tes();
  },

  beforeDestroy() {
    this.offscreenCanvas.remove();
  }
}

</script>

<style scoped>

.canvas {
  background: white;
  text-align: center;

  min-width: 220px;
  min-height: 220px;

  width: 100%;
  height: 100%;
}

canvas {
  display:block;
  pointer-events: none;
  width: 100%;
  height: 100%;
  position: absolute;
}

</style>
