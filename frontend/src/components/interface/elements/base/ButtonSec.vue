<template>
  <div class="secondButton noSelect" @click="onClick">{{ label }}</div>
</template>

<script>

export default {
  name: 'ButtonSec',
  props: ["label"],
  methods: {
    onClick() {
      this.$emit("click");
    }
  }
}
</script>

<style scoped>

.secondButton {
  background: var(--second-button-bg-color);
  border: 1px solid var(--second-button-border-color);
  border-radius: var(--button-border-radius);
  padding: 2px;
  cursor: pointer;
}

.window .secondButton {
  background: var(--window-buton-bg-color);
  border: 1px solid var(--window-buton-border-color);
}

.secondButton.disabled {
  opacity: 0.5;
  pointer-events: none;
}

</style>
