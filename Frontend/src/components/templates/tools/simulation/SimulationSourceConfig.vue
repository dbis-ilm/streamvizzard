<template>
  <div style="margin-top: 10px;">
    <div style="text-overflow: ellipsis; overflow: hidden; white-space: nowrap;"><b>{{name}}</b></div>
    <div class="contentContainer">
      <div style="padding-top: 5px;" class="title">Rate:&nbsp;</div>
      <input class="content" title="How many tuples per second should be produced" type="number" v-model="rate">
    </div>
    <div  class="contentContainer">
      <div class="title" style="padding-top: 5px;">Data:&nbsp;</div>
      <v-select class="content" :options="dataOptions" label="title" :value="data" :clearable="false" :searchable="false" @input="_onChange($event)"></v-select>
    </div>
    <div class="contentContainer" v-show="data != null && data.key === 'custom'" v-for="(i,index) in customInputs" v-bind:key="index">
      <div style="padding-top: 5px;" class="title">Socket {{index + 1}}:&nbsp;</div>
      <input class="content" title="input;chance[0,1],..." v-model="customInputs[index]">
    </div>
  </div>
</template>

<script>

export default {
  name: "SimulationSourceConfig",
  props: ["name", "id", "initialRate", "initialData", "initialCustom", "sockets"],
  data() {
    return {
      rate: 0,
      dataOptions: [{'title': 'Normal Dist', 'key': 'normalDist'},
        {'title': 'Inv Normal Dist', 'key': 'normalDistInv'},
        {'title': 'Custom', 'key': 'custom'}],
      data: null,
      customInputs: []
    }
  },
  methods: {
    _onChange(e) {
      this.data = e;
    },

    getData() {
      return {"id": this.id, "rate": parseFloat(this.rate), "data": this.data.key, "custom": this.customInputs};
    }
  },
  mounted() {
    this.rate = this.initialRate;

    if(this.initialData == null) this.data = this.dataOptions[0];
    else this.data = this.dataOptions.find(el => el.key === this.initialData);

    this.customInputs = [];
    for(let i=0; i < this.sockets; i++) this.customInputs.push("");

    if(this.initialCustom != null && this.initialCustom.length === this.customInputs.length) this.customInputs = this.initialCustom;
  }
}
</script>

<style scoped>

.title {
  width: 75px;
  text-align: left;
}

.contentContainer {
  display:flex;
  flex-direction: row;
  height: 34px;
  margin-top:5px;
}

.content {
  width: calc(100% - 75px);
  box-sizing: border-box;
}

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
