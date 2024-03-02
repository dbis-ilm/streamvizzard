<template>
  <div class="socket" :class="[type, socket.name] | kebab" :title="name + '\n' + tooltipMessage" :style="style"></div>
</template>

<script>
import {clamp} from "@/scripts/tools/Utils";

export default {
  props: ['type', 'socket', 'name'],
  data() {
    return {
      tooltipMessage: "",
      style: ""
    }
  },

  methods: {
    updateMessageCount(msg, max) {
      this.tooltipMessage = msg + " / " + max + " tuples";
      this.style = "transform: scale(" + (1 + clamp((msg / max), 0, 1) * 0.5) + ");";

      if(msg >= max) this.style += " border: 2px solid red;";
    },

    reset() {
      this.style = "";
      this.tooltipMessage = "";
    }
  }
}
</script>

<style scoped>
.socket {
  display: inline-block;
  cursor: pointer;
  border: 2px solid #828282;
  border-radius: 12px;
  width: 24px;
  height: 24px;
  margin: 6px;
  vertical-align: middle;
  background: #96b38a;
  z-index: 2;
  box-sizing: border-box; }
  .socket:hover {
    border-width: 4px; }
  .socket.multiple {
    border-color: yellow; }
  .socket.output {
    margin-right: -12px; }
  .socket.input {
    margin-left: -12px; }

</style>
