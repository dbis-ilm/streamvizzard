<template>
  <div id="spinnerContainer">
    <div class="loader"></div>
  </div>
</template>

<script>

export default {}

</script>

<style scoped>

#spinnerContainer > .loader {
  width: 20px;
  height: 20px;
  margin: 0;
}

#spinnerContainer > .loader:after {
  background: var(--second-bg-color);
}

</style>
