<template>
  <div class="contextMenuItem search">
    <input ref="input" v-model="value" placeholder="Search"/>
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
}
</script>


<style scoped>
.search input {
  width: 100%;
  box-sizing: border-box;
  text-align: center;
}
.search:hover {
  background-color: var(--main-font-color);
}

</style>
