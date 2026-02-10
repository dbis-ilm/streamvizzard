<script>

import EditorHistory from "@/components/utils/editorHistory/EditorHistory.vue";
export default {
  extends: EditorHistory,

  mounted() {
    // Register manual redo/undo

    document.addEventListener('keydown', (event) => {
      if (event.key && event.key === 'z') this.userUndo();
      else if(event.key && event.key === 'y') this.userRedo();
    });
  },

  methods: {
    async userUndo() {
      let event = this.peekNextUndo();
      if(event == null) return;

      let hadEffect = await this.performUndo();

      // Undo all events that occurred at the same time (~within 100 ms)
      // If an event has no effect, we immediately undo the next event as well

      while(this.hasUndo()) {
        let nextUndo = this.peekNextUndo();

        if(Math.abs(nextUndo.time - event.time) > 100 && hadEffect) break;
        hadEffect = await this.performUndo();
      }
    },

    async userRedo() {
      let event = this.peekNextRedo();
      if(event == null) return;

      let hadEffect = await this.performRedo();

      // Redo all events that occurred at the same time (~within 100 ms)
      // If an event has no effect, we immediately redo the next event as well

      while(this.hasRedo()) {
        let nextRedo = this.peekNextRedo();

        if(Math.abs(nextRedo.time - event.time) > 100 && hadEffect) break;
        hadEffect = await this.performRedo();
      }
    }
  }
}
</script>
