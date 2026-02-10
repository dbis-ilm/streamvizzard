<template>
  <div>
    <div>
      <CollapseHeader :openedDir="'up'" class="sectionHeader" style="position: relative;" v-model="$streamvizzard.debugger.showSidebar" title="Breakpoints">
        <i class="bi bi-plus-circle clickableIcon moreIcon" title="Add breakpoint" @click="_addBreakPointEntry($event)"></i>
      </CollapseHeader>

      <div ref="breakPointEntries" class="breakpointEntries" v-show="$streamvizzard.debugger.showSidebar">
        <SidebarBreakpoint v-for="item in operator.breakPoints" :key="item.id" :breakpoint="item" @onRemove="_onBreakPointRemove"></SidebarBreakpoint>
      </div>
    </div>
  </div>
</template>

<script>

import SidebarBreakpoint from "@/components/features/debugger/sidebar/SidebarBreakpoint.vue";
import CollapseHeader from "@/components/interface/elements/base/CollapseHeader.vue";
import {DEBUG_STEPS} from "@/scripts/features/debugger/DebugSteps";
import {v4} from "uuid";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";

export default {
  components: {CollapseHeader, SidebarBreakpoint},
  props: {
    operator: {type: SvOperator, required: true},
  },

  methods: {
    _addBreakPointEntry(event) {
      this.operator.breakPoints.push({"id": v4(), "enabled": false, "amount": 1, "type": Object.keys(DEBUG_STEPS)[0], "triggered": false})

      event.stopPropagation();

      this.$streamvizzard.debugger.showSidebar = true;
    },

    _onBreakPointRemove(bp) {
      let idx = this.operator.breakPoints.findIndex(b => b.id === bp.id);
      if(idx >= 0) this.operator.breakPoints.splice(idx, 1);
    }
  },
}

</script>

<style scoped>

.breakpointEntries {
  margin-top: 10px;
  margin-bottom: 10px;
}

.moreIcon {
  position: absolute;
  padding-left: 7px;
}

</style>