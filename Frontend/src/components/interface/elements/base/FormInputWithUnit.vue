<template>
  <div>
    <input class="formInputField limitedText alignLeft" @input="onInput" @change="onChange" :type="type" :readonly="readonly" :placeholder="placeholder" :value="inputVal" :style="'padding-right:' + unitWidth + ';'"/>
    <span class="noSelect disabled">{{unit}}</span>
  </div>
</template>

<script>

export default {
  name: 'FormInputWithUnit',
  props: ["type", "readonly", "value", "unitWidth", "unit", "placeholder"],

  computed: {
    inputVal() {
      return this.value;
    }
  },

  methods: {
    onInput(e) {
      this.$emit("input", e.target.value);
    },

    onChange(e) {
      this.onInput(e);

      this.$emit("change", e.target.value);
    }
  }
}
</script>

<style scoped>

div {
  position: relative;
  display: flex;
}

input {
  width: 100%;
}

span {
  position: absolute;
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
}

</style>
