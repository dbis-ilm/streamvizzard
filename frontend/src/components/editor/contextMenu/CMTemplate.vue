<script>

import {Services} from "@/scripts/services/Services";

export default {
  props: { delay: { type: Number, required: true }},

  data() {
    return {
      timeoutHide: () => {}
    }
  },

  methods: {
    cancelHide() {
      if (this.timeoutHide && this.timeoutHide.cancel) this.timeoutHide.cancel();
    },

    delayedHide(ms) {
      let timeout;

      return () => {
        clearTimeout(timeout);
        timeout = setTimeout(this.hide, ms);
      }
    }
  },
  mounted() {
    this.timeoutHide = this.delayedHide(this.delay);

    this.cancelHide();

    this.$nextTick(() => {
      let visRes = this.$streamvizzard.editor.isFullyVisible(this.$el);

      this.menu.posX += Math.min(visRes.rightDif, 0);
      this.menu.posY -= Math.min(visRes.topDif, 0);
      this.menu.posX -= Math.min(visRes.leftDif, 0);
      this.menu.posY += Math.min(visRes.botDif, 0);
    });

    Services.EditorInputManager.onInputSelected(this.$el);
  },

  beforeDestroy() {
    Services.EditorInputManager.onInputDeselected();
  }
}

</script>
