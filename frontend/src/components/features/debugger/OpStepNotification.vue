<template>
  <transition name="notificationFade">
    <div v-if="operator != null" class="notification"
         :style="'left: ' + (operator.posX + operator.width / 2) + 'px; top: ' + operator.posY + 'px;' +
          'transform: translate(-50%, -100%);'">
      <b>{{(stepEx.undo != null ? (stepEx.undo ? "Undo ": "Redo ") : "")}}</b>{{descriptor}}<div class='arrow'><span></span></div>
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

  computed: {
    descriptor() {
      return getStepDescriptionForType(this.stepEx.step.type);
    },
  },

  mounted() {
    setTimeout(() => {
      if(this.operator.debugStepNotification === this.stepEx)
        this.operator.debugStepNotification = null;
      }, 1500); // Schedule removal
  }
}

</script>
