<template>
  <div class="breakPointEntry">
    <input title="Enable breakpoint" type="checkbox" v-model="activated" @change="_onEnableChanged" style="float:left; margin-left: 0; margin-top: 2px; margin-right: 10px; cursor: pointer;"/>
    <v-select v-auto-blur class="select" :options="selectOptions" :value="selectedValue" label="title" :clearable="false" :searchable="false" @input="_onSelectChanged" style="flex: 1;"></v-select>
    <input type="number" placeholder="Unset" v-model="number" @change="_onNumberChanged" style="width:50px; margin-left: 5px;"
           title="After how many occurrences of this event the breakpoint should trigger" />
    <i title="Remove breakpoint" @click="_onRemove" class="bi bi-x-circle clickableIcon" style="margin-top: 2px; margin-left: 5px;"></i>
  </div>
</template>

<script>
import {getDropdownData} from "@/scripts/tools/debugger/DebugSteps";

export default {
  name: "sidebarBreakpoint",
  props: ["index", "data"],

  data() {
    return {
      activated: false,
      selectOptions: getDropdownData(),
      selectedValue: null,
      number: 1
    }
  },

  methods: {
    getData() {
      return {
        "enabled": this.activated,
        "type": this.selectedValue.key,
        "amount": this.number
      }
    },

    _onEnableChanged() {
      this.$emit("onChange", this);
    },

    _onNumberChanged() {
      this.number = isNaN(parseInt(this.number)) ? 1 : parseInt(this.number);
      this.$emit("onChange", this);
    },

    _onSelectChanged(event) {
      this.selectedValue = event;

      this.$emit("onChange", this);
    },

    _onRemove() {
      this.$emit("onRemove", this.index);
    }
  },

  mounted() {
    this.selectedValue = this.selectOptions[0];

    if(this.data != null) {
      this.activated = this.data.enabled;
      this.selectedValue = this.selectOptions.find(o => o.key === this.data.type);
      this.number = this.data.amount;
    }
  }
}
</script>

<style scoped>

.breakPointEntry {
  display:flex;
  height: 25px;

  margin-bottom: 6px;
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

<style>
.breakPointEntry .select .vs__search, .breakPointEntry .select .vs__search:focus, .breakPointEntry .select .vs__selected {
  margin: 0 !important;
}

.breakPointEntry .select .vs__dropdown-toggle {
  padding: 0;
}
</style>
