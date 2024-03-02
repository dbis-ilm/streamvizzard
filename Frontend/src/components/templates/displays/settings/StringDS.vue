<template>
<div :title="desc" class="displayModeSetting">
  <div class="displayModeSettingTitle">{{ name }}&nbsp;</div>
  <input type="text" placeholder="Unset" v-model="value" @input="onChange" class="displayModeSettingOption"/>
  <i title="Reset" @click="reset" class="bi bi-x-circle displayModeSettingReset"></i>
</div>
</template>

<script>
export default {
  name: "StringDS",
  props: ["name", "value", "skey", "change", "desc", "default"],

  methods: {
    onChange() {
      this.change(this.skey, this.value);
    },

    reset() {
      this.value = this.default;

      this.onChange();
    }
  }
}
</script>

<style scoped>

</style>
