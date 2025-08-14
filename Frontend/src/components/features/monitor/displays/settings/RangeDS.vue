<template>
<div :title="desc" class="displayModeSetting">
  <div class="displayModeSettingTitle">{{ name }}&nbsp;</div>
  <input type="number" placeholder="Unset" v-model="val1" @input="onChange" class="displayModeSettingOption"/>&nbsp;
  <input type="number" placeholder="Unset" v-model="val2" @input="onChange" class="displayModeSettingOption"/>
  <i title="Reset" @click="reset" class="bi bi-x-circle displayModeSettingReset"></i>
</div>
</template>

<script>
export default {
  name: "RangeDS",
  props: ["name", "value", "skey", "change", "desc", "default"],
  data() {
    return {
      val1: null,
      val2: null
    }
  },

  methods: {
    onChange() {
      this.value = [this.val1 != null ? parseFloat(this.val1) : null, this.val2 != null ? parseFloat(this.val2) : null];

      this.change(this.skey, this.value);
    },

    reset() {
      this.value = this.default;

      this.val1 = this.value != null ? this.value[0] : null;
      this.val2 = this.value != null ? this.value[1] : null;

      this.onChange();
    }
  },

  mounted() {
    this.val1 = this.value != null ? this.value[0] : null;
    this.val2 = this.value != null ? this.value[1] : null;
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
