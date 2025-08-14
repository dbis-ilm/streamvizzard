<template>
  <div class="inspectContainer" ref="container"></div>
</template>

<script>
import $ from 'jquery'
import Vue from "vue";
import StructureInspectElement from "@/components/features/monitor/displays/inspect/StructureInspectElement.vue";

export default {
  name: "StructureInspect",
  data() {
    return {
      structureElements: [],
      selectedStructureElement: null,
    }
  },
  methods: {
    setStructureData(data) {
      if(data == null) {
        this.reset();
      } else {
        this.reset();

        this.buildElements(data, this.$refs.container);

        $(this.$refs.container).find('.inspectElementToggle').each(function() {
          toggleElement($(this), false);
        })
      }
    },

    buildElements(root, container) {
      if(typeof root === "object" && !Array.isArray(root)) { //Dict
        for(let key in root) {
          let c = this._createElement(key, container);

          this.buildElements(root[key], c);

          let cj = $(c);

          if(cj.children(".inspectElement").length === 0) {
            cj.children(".inspectElementToggle").hide();

            //Set type info
            cj.children(".inspectElementType").html(root[key]);
          }
        }
      } else if(Array.isArray(root)) {
        for(let i=0; i < root.length; i++) {
          let c = this._createElement("[" + i + "]", container);

          this.buildElements(root[i], c);
        }
      }
    },

    _createElement(key, appendTo) {
      const componentClass = Vue.extend(StructureInspectElement);
      const instance = new componentClass({
        propsData: {value: key}
      });

      instance.$on("select", this.onElementSelected);

      this.structureElements.push(instance);

      instance.$mount();

      return appendTo.appendChild(instance.$el);
    },

    onElementSelected(data) {
      this.$emit('selected', data);
    },

    reset() {
      for(let i = 0; i < this.structureElements.length; i++) {
        let elem = this.structureElements[i];

        elem.$el.remove();
        elem.$destroy();
      }

      this.structureElements = [];
    },
},
}

function toggleElement(toggle, show) {
  if(show) {
    toggle.addClass("shown");
    toggle.html("-");
  } else {
    toggle.removeClass("shown");
    toggle.html("+");
  }

  toggle.closest('.inspectElement').children('.inspectElement').each(function() {
    if(show) $(this).show();
    else $(this).hide();
  });
}

$( document ).on( "click", ".inspectElementToggle", function() {
  let toggle = $(this);

  toggleElement(toggle, !toggle.hasClass("shown"));
});

</script>
