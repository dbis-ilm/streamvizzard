<template>
  <div>
    <div id="heatmap" class="heatmapComponent" ref="container"></div>
    <div id="heatmapStats" class="heatmapComponent" v-if="hmType !== 0">
      <div style="text-align: left;"><b>Heatmap Info</b></div>
      <div style="text-align:left; margin-top:10px;">Unit: {{unit}}</div>
      <div class="heatmapGradient">
        <div class="heatmapLegendMark" style="top:-0.2em; left:48px;">{{minVal}}</div>
        <div class="heatmapLegendMark" style="bottom:-0.2em; left:48px;">{{maxVal}}</div>
        <div id="heatmapLegendSteps" style="left:48px;"></div>
      </div>
    </div>
  </div>
</template>

<script>
import $ from "jquery";
import HeatmapNode from './HeatmapNode.vue'
import Vue from "vue";

let heatMap = null;
const nodeLookup = {};

let hmStepElements = null;
let hmStepContainer = null;

export default {
  name: "HeatmapTemplate",
  data() {
    return {
      minVal: "0",
      maxVal: "0",
      unit: "",
      hmType: 0
    }
  },
  mounted() {
    //Append to editor in the background (after pageLoad)
    document.addEventListener("DOMContentLoaded", function(){
      $('#heatmap').appendTo($("#rete > div"));
    });

    this.hide();

    heatMap = this;
  },
  methods: {
    initialize(editor, shown) {
      editor.on('nodetranslated', node => {
        this.onNodeUpdated(node.node);
      });

      editor.on('nodecreated', node => {
        this.registerNode(node.vueContext, node); //After DOM load
      });

      editor.on('noderemoved', node => {
        this.onNodeDeleted(node);
      });

      if(shown) this.show();
      else this.hide();
    },
    onNodeUpdated(node) {
      nodeLookup[node.id].updateNode();
    },
    onNodeDeleted(node) {
      const elem = nodeLookup[node.id];
      elem.$el.remove();
      elem.$destroy();

      delete nodeLookup[node.id];
    },
    registerNode(vueNode, node) {
      const componentClass = Vue.extend(HeatmapNode);
      const instance = new componentClass({
        propsData: {vueNode: vueNode, node: node}
      });

      instance.$mount();

      heatMap.$refs.container.appendChild(instance.$el);

      nodeLookup[node.id] = instance;

      instance.updateNode();
    },
    show(type) {
      this.hmType = type;

      let comp = $('.heatmapComponent');
      comp.css('display', 'block');
      comp.parent().addClass("heatmapActive");

      if(type === 1) this.unit = "msecs";
      else if(type === 2) this.unit = "kbytes";
      else if(type === 3) this.unit = "msecs";
    },
    hide() {
      this.hmType = 0;
      let comp = $('.heatmapComponent');
      comp.css('display', 'none');
      comp.parent().removeClass("heatmapActive");
      //this.$el.style.display = "none";
    },
    onDataUpdate(min, max, steps) {
      this.minVal = min.toFixed(2);
      this.maxVal = max.toFixed(2);

      if(hmStepContainer == null) hmStepContainer = $('#heatmapLegendSteps');
      let gradientHeight = $('.heatmapGradient').height();

      //Clear previous steps if number changed
      if(hmStepElements != null && hmStepElements.length !== steps.length) {
        hmStepElements.remove();
        hmStepElements = null;
      }

      //Create elements if not present
      if(hmStepElements == null) {
        for(let i=0; i < steps.length; i++)  {
          hmStepContainer.append('<div class="hmLegendStep" style="position:absolute;"><div>');
        }

        hmStepElements = hmStepContainer.find('.hmLegendStep');
      }

      hmStepElements.each(function(index) {
        let step = steps[index];

        let stepVal = step[0].toFixed(2);

        //If it's the first step and has the same as the min value we hide it
        if(index === 0 && stepVal === heatMap.minVal) $(this).hide();
        else $(this).show();

        let stepPos = step[1];
        let ypos = Math.round(gradientHeight * stepPos);

        $(this).css("top", "calc(" + ypos + "px - 0.5em)").text(stepVal);
      })
    }
  }
}

</script>

<style scoped>
.heatmapLegendMark, #heatmapLegendSteps {
  text-align:left;
  white-space: nowrap;
  position: absolute;
}

.heatmapGradient {
  position: relative;
  margin: 5px 10px 10px 10px;
  height:200px;
  width: 40px;

  background: linear-gradient(180deg, rgba(0,200,255,1) 0%, rgba(255,255,100,1) 33%, rgba(255,100,100,1) 66%, rgba(255,100,255,1) 100%);
}

#heatmap {
  position: absolute;
  z-index: -50;
}
</style>
