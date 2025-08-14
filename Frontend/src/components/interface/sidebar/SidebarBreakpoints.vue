<template>
<div class="sidebarNodeBreakpoints" v-if="system != null && system.debuggerEnabled">
  <div class="sidebarNodeBreakpointTitle"><b>Breakpoints</b><i class="bi bi-plus-circle clickableIcon moreIcon" title="Add breakpoint" @click="_addEntry(null)"></i></div>

  <div ref="breakPointEntries" class="sidebarNodeBreakpointEntries">
    <SidebarBreakpoint v-for="(item, index) in entries" v-bind:key="index" :data="item" :index="index" ref="breakPoints"
      @onRemove="_onRemoveEntry" @onChange="_sendDataUpdate"></SidebarBreakpoint>
  </div>
</div>
</template>

<script>

import SidebarBreakpoint from "@/components/interface/sidebar/SidebarBreakpoint.vue";
import {system} from "@/main";
import {DEBUG_STEPS} from "@/scripts/tools/debugger/DebugSteps";
import Vue from "vue";

export default {
  name: "sidebarBreakpoints",
  components: {SidebarBreakpoint},
  data() {
    return {
      system: null,
      entries: []
    }
  },

  methods: {
    load(bps) {
      this.reset();

      let elm = this;
      Vue.nextTick(function () {
        elm.entries = bps;
      })

    },

    reset() {
      this.entries = [];
    },

    _addEntry(loaded = null) {
      if(loaded != null) this.entries.push(loaded);
      else this.entries.push({"enabled": false, "amount": 1, "type": Object.keys(DEBUG_STEPS)[0]})

      let elm = this;
      Vue.nextTick(function () {
        elm._sendDataUpdate();
      })
    },

    _sendDataUpdate() {
      let data = []

      for(let i=0; i < this.entries.length; i++) {
        data.push(this.$refs.breakPoints[i].getData());
      }

      this.$emit("onChange", data);
    },

    _onRemoveEntry(index) {
      this.entries.splice(index, 1);

      this._sendDataUpdate();
    }
  },

  mounted() {
    this.system = system;
  }
}
</script>

<style scoped>

.sidebarNodeBreakpoints {
  margin-top: 15px;
}

.sidebarNodeBreakpointEntries {
  margin-top: 10px;
  margin-bottom: 10px;
}

.sidebarNodeBreakpointTitle {
  text-decoration: underline;
  position: relative;
}

.moreIcon {
  position: absolute;
  padding-left: 7px;
}

</style>
