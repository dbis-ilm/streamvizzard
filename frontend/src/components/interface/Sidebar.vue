<template>
  <div id="sidebar" :class="['dock', $streamvizzard.interface.showSidebar && 'opened']">
    <div class="opContent" v-if="operator != null" v-show="$streamvizzard.interface.showSidebar">
      <div class="title limitedText" :title="'Operator: ' + operator.definition.displayName">{{ operator.name }}
        <span class="titleID" :title="operator.uuid">{{ operator.id }}</span>
        <hr>
      </div>

      <div class="sidebarContent">

        <div v-if="operator.errorMsg != null" class="sectionOffset errorMsg">
          <div class="sectionHeader">Error</div>
          <div class="errorContent limitedText" :title="operator.errorMsg">{{ operator.errorMsg }}</div>
        </div>

        <MonitorSidebarOp :operator="operator" v-if="$streamvizzard.monitor.enabled && !$streamvizzard.compiler.enabled" class="sectionOffset"/>

        <AdvisorSidebarOp :operator="operator" v-if="$streamvizzard.advisor.enabled && !$streamvizzard.compiler.enabled" class="sectionOffset"/>

        <DebugSidebarOp :operator="operator" v-if="$streamvizzard.debugger.enabled && !$streamvizzard.compiler.enabled" class="sectionOffset"/>

        <CompileSidebarOp :operator="operator" v-if="$streamvizzard.compiler.enabled" class="sectionOffset"/>
      </div>
    </div>

    <div @click="_toggleWindow" :class="'openCloseButton right ' + ($streamvizzard.interface.showSidebar ? 'opened' : 'closed')"
         title="Open/Close the operator sidebar">
      <i :class="'bi ' + ($streamvizzard.interface.showSidebar ? 'bi-caret-right-fill' : 'bi-caret-left-fill')"></i>
    </div>

  </div>
</template>

<script>

import CompileSidebarOp from "@/components/features/compiler/CompileSidebarOp.vue";
import DebugSidebarOp from "@/components/features/debugger/sidebar/DebugSidebarOp.vue";
import AdvisorSidebarOp from "@/components/features/advisor/AdvisorSidebarOp.vue";
import MonitorSidebarOp from "@/components/features/monitor/sidebar/MonitorSidebarOp.vue";

export default {
  components: {MonitorSidebarOp, AdvisorSidebarOp, DebugSidebarOp, CompileSidebarOp},
  name: "Sidebar",

  computed: {
    operator() {
      return this.$streamvizzard.editor.selectedOperator;
    }
  },

  methods: {
    _toggleWindow() {
      this.$streamvizzard.interface.showSidebar = !this.$streamvizzard.interface.showSidebar;
    },
  }
}

</script>

<style>

#sidebar hr {
  color: var(--main-border-color);
}

#sidebar .sectionHeader {
  font-weight: bold;
  text-decoration: underline;
}

#sidebar .vOffset {
  margin-top: 15px;
}

</style>

<style scoped>

#sidebar {
  height: 100%;
  max-height: 100%;
  border-left: 2px solid var(--main-border-color);
  background: var(--second-bg-color);

  position: fixed;
  right: 0;

  cursor: default;
}

#sidebar.opened {
  width: 350px;
}

#sidebar .opContent {
  padding-top : 6px;
  height: 100%;
}

#sidebar .title {
  font-weight: bold;
  font-size: 1.1rem;

  padding-left: 15px;
  padding-right: 15px;
  margin-bottom: -10px;
}

#sidebar .titleID {
  float: right;
  position: absolute;
  right: 6px;
  font-size: 12px;
  top: 0;
}

#sidebar .sidebarContent {
  margin-top: 10px;
  overflow-y: auto;
  height: calc(100% - 7rem);

  scrollbar-gutter: stable both-edges;
  padding-right: 15px;
  padding-left: 15px;
}

.sidebarContent .sectionOffset:not(:first-child) {
  margin-top: 15px;
}

.errorContent {
  margin-top: 5px;
  white-space: break-spaces;
  font-style: italic;
  max-height: 4.2em;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 5px;
}

</style>
