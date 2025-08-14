<template>
  <label class="file-select">
    <div class="select-button" style="overflow: hidden; text-overflow: ellipsis; text-align:center;">
      <span v-if="value">{{value.name}}</span>
      <span v-else>{{ selectTitle }}</span>
    </div>
    <input type="file" :accept="extensions" @change="handleFileChange"/>
  </label>
</template>

<script>
//https://www.digitalocean.com/community/tutorials/vuejs-file-select-component
export default {
  props: {
    value: File,
    extensions: null,
    selectTitle: String,
  },
  methods: {
    handleFileChange(e) {
      let reader = new FileReader();
      reader.readAsText(e.target.files[0],'UTF-8');

      // here we tell the reader what to do when it's done reading...
      reader.onload = readerEvent => {
        let content = readerEvent.target.result; // this is the content!

        this.$emit('input', content)
      }
    }
  }
}
</script>

<style scoped>
.file-select > .select-button {
  height: 2rem;
  border: 1px solid var(--main-border-color);
  border-radius: var(--button-border-radius);
  text-align: center;
  cursor: pointer;
}

.file-select > .select-button > span {
  line-height: 100%;
  display: block;
  height: 100%;
  padding-top: 0.5rem;
}

.file-select > input[type="file"] {
  display: none;
}
</style>
