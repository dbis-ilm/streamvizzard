<template>
  <transition name="notificationFade">
    <div v-if="operator != null" class="notification"
         :style="'left: ' + (operator.posX + operator.width / 2) + 'px; top: ' + operator.posY + 'px;' +
          'transform: translate(-50%, -100%);'">
      <span :class="[updateMode && 'updateText', updateModeStart && 'startUpdateText']" @animationend="updateCompleted">
        <b>{{(stepEx.undo != null ? (stepEx.undo ? "Undo ": "Redo ") : "")}}</b>{{descriptor}}
      </span><div class='arrow'><span></span></div>
    </div>
  </transition>
</template>

<script>

import {DebugStepExecution, getStepDescriptionForType} from "@/scripts/features/debugger/DebugSteps";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";

export default {
  props: {
    stepEx: {type: DebugStepExecution, required: true},
    operator: {type: SvOperator, required: true},
  },

  data() {
    return {
      updateMode: false,
      updateModeStart: false,
    }
  },

  watch: {
    stepEx() {
      this.setupTimeout();

      // Trigger fadeIn of new step info

      if(this.updateTimeout != null) return;

      this.updateMode = false;
      this.updateModeStart = true;

      this.updateTimeout = setTimeout(() => {
        this.updateMode = true;
        this.updateModeStart = false;
      }, 50);
    }
  },

  computed: {
    descriptor() {
      return getStepDescriptionForType(this.stepEx.step.type);
    },
  },

  methods: {
    updateCompleted() {
      this.updateTimeout = null; // Clear for next update fade
    },

    setupTimeout() {
      if(this.timeout != null) clearTimeout(this.timeout);

      this.timeout = setTimeout(() => {
        if(this.operator.debugStepNotification === this.stepEx)
          this.operator.debugStepNotification = null;
      }, 1500); // Schedule removal
    }
  },

  mounted() {
    this.setupTimeout();
  }
}

</script>

<style scoped>

.startUpdateText {
  opacity: 0;
}

.updateText {
  animation: fadeIn 250ms ease-in-out;
}

@keyframes fadeIn {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

</style>
