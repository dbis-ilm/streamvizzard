<template>
<div :title="desc" class="displayModeSetting">
  <div class="displayModeSettingTitle">{{ name }}&nbsp;</div>
  <div class="displayModeSettingOption"><input type="checkbox" v-model="value" @input="onChange($event)" style="float:left; margin-left: 0; margin-top: 5px;"/></div>
  <i title="Reset" @click="reset" class="bi bi-x-circle displayModeSettingReset"></i>
</div>
</template>

<script>
export default {
  name: "BoolDS",
  props: ["name", "value", "skey", "change", "desc", "default"],

  methods: {
    onChange(e) {
      if(e !== undefined) this.value = e.target.checked;
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
