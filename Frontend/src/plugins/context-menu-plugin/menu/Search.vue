<template>
  <div class="contextMenuItem search">
    <input ref="input" class="mouseEventBlocker" v-model="value" placeholder="Search"/>
  </div>
</template>

<script>

export default {
  props: ['search'],
  data() {
    return {
      value: null
    }
  },
  watch: {
    value() {
      this.$emit('search', this.value);
    }
  },

  methods: {
    onHide() {
      this.$refs.input.blur(); //Require or otherwise mouseEventBlocker will not be reset
    }
  }
}
</script>


<style scoped>
.search input {
  width: 100%;
  box-sizing: border-box;
  text-align: center;
}
.search:hover {
  background-color: #444;
}

</style>
