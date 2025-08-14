<template>
  <div class='inspectElement'>
    <span class='inspectElementToggle'>+</span>
    <span class='inspectElementKey' @click="selectElement($event)">{{ value }}</span>
    <span class="inspectElementType"></span>
  </div>
</template>

<script>
import $ from "jquery";

export default {
  name: "StructureInspectElement",
  props: ['value'],
  methods: {
    selectElement(el) {
      let element = $(el.target);

      let old = element.closest('.inspectContainer').find('.inspectElementKey.selected');
      old.removeClass("selected");

      if(!old.is(element)) {
        element.addClass("selected");

        //Retrieve key by iterating up
        let key = element.html();
        let current = element.parent(".inspectElement");

        while(current.length !== 0) {
          current = current.parent('.inspectElement');
          if(current.length === 0) break;

          key = current.find(".inspectElementKey").html() + ">" + key;
        }

       this.$emit('select', key);
      } else this.$emit('select', "") //Nothing selected
    },
  }
}
</script>

<style>

.inspectElement {
  text-align: left;
  margin-left:15px;

  clear: both;

  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.inspectElementKey.selected {
  font-weight: bold;
  color: blue;
}

.inspectElementKey {
  cursor: pointer;
}

.inspectElementToggle {
  width:40px;
  height:40px;

  cursor: pointer;

  padding-right:10px;
}

.inspectElementType {
  float: right;
  font-style: italic;

  margin-right: 15px;
}

</style>
