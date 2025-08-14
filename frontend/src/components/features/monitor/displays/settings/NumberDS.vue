<template>
<div :title="desc" class="displayModeSetting">
  <div class="displayModeSettingTitle">{{ name }}&nbsp;</div>
  <input type="number" placeholder="Unset" v-model="value" @input="onChange" class="displayModeSettingOption"/>
  <i title="Reset" @click="reset" class="bi bi-x-circle displayModeSettingReset"></i>
</div>
</template>

<script>
export default {
  name: "NumberDS",
  props: ["name", "value", "skey", "change", "desc", "default"],

  methods: {
    onChange() {
      this.change(this.skey, this.value != null ? parseFloat(this.value) : null);
    },

    reset() {
      this.value = this.default;

      this.onChange();
    }
  }
}
</script>

<style scoped>

/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox */
input[type=number] {
  -moz-appearance: textfield;
}

</style>
