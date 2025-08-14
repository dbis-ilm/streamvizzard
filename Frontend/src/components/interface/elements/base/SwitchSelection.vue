<template>
  <div class="formSwitch noSelect">
    <div v-for="option in optionData" :key="option.value" :title="option.title"
         @click="onSelect(option.value);" :class="value === option.value ? 'selected' : ''">{{ option.label }}</div>
  </div>
</template>

<script>

export default {
  name: 'SwitchSelection',
  props: ["value", "optionData"],

  methods: {
    onSelect(option) {
      this.$emit("input", option);
    }
  }
}
</script>

<style scoped>

.formSwitch {
  display: table;
  table-layout: fixed;
  width: 100%;
  margin-top: 10px;
}

.formSwitch .selected {
  background-color: var(--main-font-color) !important;
  color: white;
}

.formSwitch > div {
  display: table-cell;
  background-color: var(--second-button-bg-color);
  border: 1px solid var(--main-border-color);
  cursor: pointer;
  padding: 2px;
}

.formSwitch > div:first-child {
  border-top-left-radius: var(--button-border-radius);
  border-bottom-left-radius: var(--button-border-radius);
}

.formSwitch > div:last-child {
  border-top-right-radius: var(--button-border-radius);
  border-bottom-right-radius: var(--button-border-radius);
}

</style>
