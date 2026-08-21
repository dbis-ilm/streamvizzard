<script>

import ConnectionTemplate from "@/components/pipeline/connection/ConnectionTemplate.vue";

export default {
  extends: ConnectionTemplate,

  computed: {
    hoverTitle() {
      return ""; // Override parent
    },

    focused() {
      return false; // Override parent
    }
  },

  methods: {
    _onPointerUp(e) {
      if(this.$streamvizzard.editor.pickedConnection != null) {
        e.stopPropagation();
        e.preventDefault();

        this.$streamvizzard.editor.unpickSocketConnection(null);
      }
    },

    _onPointerMove() {
      if(this.$streamvizzard.editor.pickedConnection != null)
        this.updatePathData();
    },

    _onMouseOver() {
      // Override parent
    },

    _onMouseOut() {
      // Override parent
    }
  },

  mounted() {
    window.addEventListener("pointerup", this._onPointerUp);
    window.addEventListener("pointermove", this._onPointerMove);

    this.connection.highlighted = true;
  },

  beforeDestroy() {
    window.removeEventListener("pointerup", this._onPointerUp);
    window.removeEventListener("pointermove", this._onPointerMove);
  }
}

</script>
