<template>
  <div :class="'breakPointEntry' + (breakpoint.triggered ? ' triggered' : '')">
    <input :title="activateTooltip" type="checkbox" v-model="breakpoint.enabled" class="activateCheck" @change="_onActivateChanged"/>
    <v-select v-auto-blur class="select" :options="selectOptions" :value="selectedOption" label="title" :clearable="false" :searchable="false" @input="_onSelectChanged" style="flex: 1;"></v-select>
    <input type="number" placeholder="Unset" :value="breakpoint.amount" @change="_onNumberChanged" style="width:50px; margin-left: 5px;"
           title="After how many occurrences of this event the breakpoint should trigger" />
    <i title="Remove breakpoint" @click="_onRemove" class="bi bi-x-circle clickableIcon" style="margin-top: 2px; margin-left: 5px;"></i>
  </div>
</template>

<script>
import {getDropdownData} from "@/scripts/features/debugger/DebugSteps";

export default {
  name: "sidebarBreakpoint",
  props: ["breakpoint"],

  data() {
    return {
      selectOptions: getDropdownData(),
      selectedOption: null,
    }
  },

  methods: {
    _onActivateChanged() {
      this.breakpoint.triggered = false;
    },

    _onNumberChanged(numb) {
      // Only accept valid numbers (and only trigger reactivity when present)
      numb = numb.target.value;
      this.breakpoint.amount = isNaN(parseInt(numb)) ? 1 : parseInt(numb);
    },

    _onSelectChanged(event) {
      this.selectedOption = event;
      this.breakpoint.type = event.key;
    },

    _onRemove() {
      this.$emit("onRemove", this.breakpoint);
    }
  },

  computed: {
    activateTooltip() {
      if(this.breakpoint.triggered) return "Breakpoint triggered!";
      else return (this.breakpoint.enabled ? "Disable" : "Enable") + " breakpoint";
    }
  },

  mounted() {
    this.selectedOption = this.selectOptions.find((x) => x.key === this.breakpoint.type);
  }
}
</script>

<style scoped>

.breakPointEntry {
  display:flex;
  height: 25px;

  margin-bottom: 6px;
}

.activateCheck {
  margin-top: 4px;
  margin-right: 10px;
  cursor: pointer;
}

.triggered .activateCheck:after {
  background: red;
}

input[type=number] {
  appearance: textfield;
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
