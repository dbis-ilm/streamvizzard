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
    extensions: null
  },
  data() {
    return {
      selectTitle: "Select"
    }
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
  padding: 0.5rem;

  color: rgb(51, 51, 51);
  border: 1px solid rgba(0, 0, 0, 0.2);

  border-radius: .3rem;

  text-align: center;
}

.file-select > input[type="file"] {
  display: none;
}
</style>
