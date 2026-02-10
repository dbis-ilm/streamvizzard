<template>
  <transition name="notificationFade">
    <div class="notification"
         :style="'transform: translate(' + notification.posX + 'px, ' + notification.posY + 'px) translate(-50%, -100%);'">
      <div v-html="notification.content"></div>
      <div class='arrow'><span></span></div>
    </div>
  </transition>
</template>

<script>

import EditorNotification from "@/scripts/editor/EditorNotification";

export default {
  props: {
    notification: {type: EditorNotification, required: true},
  },

  mounted() {
    setTimeout(() => { this.$streamvizzard.editor.removeNotification(this.notification); }, this.notification.duration); // Schedule removal
  }
}

</script>
