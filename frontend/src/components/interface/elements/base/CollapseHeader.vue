<template>
  <div @click="_onClick" class="noSelect toggleHeader" :title="tooltip">{{ title }}
    <i :class="'bi ' + (open ? 'bi-caret-' + directionOpened + '-fill' : 'bi-caret-' + directionClosed + '-fill')"></i>
  </div>
</template>

<script>

export default {
  name: 'CollapseHeader',
  props: {
    openedDir: {type: String, required: true},
    value: {required: true},
    title: {type: String, required: true},
    tooltip: {type: String, default: ""},
  },

  data() {
    return {
      open: this.value,
      directionOpened: "",
      directionClosed: "",
    }
  },

  methods: {
    _onClick() {
      this.open = !this.open;

      this.$emit("input", this.open);
    }
  },

  mounted() {
    if(this.openedDir === "left") {
      this.directionOpened = "left";
      this.directionClosed = "right";
    } else if(this.openedDir === "right") {
      this.directionOpened = "right";
      this.directionClosed = "left";
    } else if(this.openedDir === "up") {
      this.directionOpened = "up";
      this.directionClosed = "down";
    } else {
      this.directionOpened = "down";
      this.directionClosed = "up";
    }
  }
}
</script>

<style scoped>

.toggleHeader {
  position: relative;
  cursor: pointer;
  text-align: center;
  width: calc(100% + 10px);
  margin-left:-5px;
}

.toggleHeader > i {
  position: absolute;
  right: 10px;
}


</style>
