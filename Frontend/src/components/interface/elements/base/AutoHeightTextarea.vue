<template>
  <textarea ref="elm" :value="value" rows="1" @change="onChange($event)" @input="onInput"></textarea>
</template>

<script>

export default {
  name: 'AutoScaleTextarea',
  props: ["value"],

  watch: {
    value() {
      // Update height after value change

      this.$nextTick(() => {
        this.onInput();
      });
    }
  },

  methods: {
    onChange(event) {
      this.$emit("change", event);
    },

    onInput() {
      this.$refs.elm.style.height = "auto";
      this.$refs.elm.style.height = this.$refs.elm.scrollHeight + "px";
    }
  },

  mounted() {
    // On initial load the scrollHeight might be off by a little, this delay fixes the calculation
    setTimeout(() => {
      this.onInput();
    }, 100);
  }
}
</script>

<style scoped>

textarea {
  min-height: 1em;
  overflow: hidden;
  box-sizing: border-box;
}

</style>
