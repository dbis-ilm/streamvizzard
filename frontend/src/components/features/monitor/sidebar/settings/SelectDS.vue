<template>
<div :title="desc" class="displayModeSetting">
  <div class="displayModeSettingTitle">{{ name }}&nbsp;</div>
  <v-select v-auto-blur :options="data" :value="value" :clearable="false" :searchable="false" @input="onChange($event)" class="displayModeSettingOption"></v-select>
  <i title="Reset" @click="reset" class="bi bi-x-circle displayModeSettingReset"></i>
</div>
</template>

<script>
export default {
  name: "SelectDS",
  props: ["name", "value", "skey", "change", "desc", "default", "data"],

  methods: {
    onChange(e) {
      this.value = e;
      this.change(this.skey, this.value);
    },

    reset() {
      this.value = this.default;

      this.onChange(this.default);
    }
  }
}
</script>

<style>

.displayModeSetting .vs__search, .displayModeSetting .vs__search:focus, .displayModeSetting .vs__selected {
  margin: 0 !important;
}

.displayModeSetting .vs__dropdown-toggle {
  padding: 0;
}

</style>
