<script>

import EditorHistory from "@/components/utils/editorHistory/EditorHistory.vue";
export default {
  name: "UserEditorHistory",
  extends: EditorHistory,

  methods: {
    initialize(editor) {
      // Call super function
      EditorHistory.methods.initialize.call(this, editor);

      // Register manual redo/undo

      let t = this;

      document.addEventListener('keydown', function(event) {
        if (event.ctrlKey && event.key === 'z') t.performUndo();
        else if(event.ctrlKey && event.key === 'y') t.performRedo();
      });
    },
  }
}
</script>
