<template>
  <div class="compileStrategySelect">
    <div class="compileStrategyOptions">
      <div :style="showStrategySelect ? '' : 'margin-top: -10px;'">
        <div class="formInputContainer" v-if="showStrategySelect">
          <span class="formInputLabel limitedText alignLeft" title="Strategy used for calculating compilation target suggestions for each operator">Strategy:&nbsp;</span>
          <v-select v-auto-blur :clearable="false" :searchable="false" :options="strategyOptions" class="formInputField"
                    :value="strategyOptionSelected" @input="_onStrategySelected($event)" label="title" :getOptionKey="(o) => o.key">
          </v-select>
        </div>

        <CollapseHeader v-if="strategyOptionSelected != null && toggleSettings" :openedDir="'up'" class="settingsToggle" v-model="showSettings" :title="'Settings'"></CollapseHeader>

        <div class="optionsContainer" v-if="strategyOptionSelected != null && (showSettings || !toggleSettings)">
          <div class="formInputContainer" v-for="el in strategyOptionSelected.elements" :key="el.key" v-show="el.show">
            <span v-if="el.type !== 'Grouper'" class="formInputLabel limitedText alignLeft" :title="el.tooltip">{{ el.title }}:&nbsp;</span>
            <CollapseHeader v-else :openedDir="'up'" class="optionsGrouper" v-model="el.open" @input="() => el.onToggle()" :title="el.title" :tooltip="el.tooltip"></CollapseHeader>

            <v-select v-if="el.type === 'Select'" v-auto-blur :getOptionKey="(o) => o.key" :clearable="false"
                      :searchable="false" :options="el.options" class="formInputField"
                      :value="el.value" @input="(v) => el.onValueChange(v)" label="title"></v-select>
            <input v-else-if="el.type === 'TextInput'" class="formInputField alignLeft optionTextInput" type="text" v-model="el.value" :placeholder="el.placeholder" @change="(event) => el.onValueChange(event.target.value)"/>
            <div v-else-if="el.type === 'Checkbox'" class="formInputField" style="border: initial;"><input type="checkbox" class="optionCheckbox" :checked="el.value" @change="(event) => el.onValueChange(event.target.checked)"/></div>
            <vue-slider v-else-if="el.type === 'Slider'" v-model="el.value" v-bind="sliderOptions" @change="(v) => el.onValueChange(v)" class="formInputField optionSlider"></vue-slider>
            <FormInputWithUnit v-else-if="el.type === 'TextInputUnit'" :type="'text'" :readonly="false" v-model="el.value" :unit="el.unit" :unitWidth="el.unitWidth" :placeholder="el.placeholder" @change="(v) => el.onValueChange(v)"></FormInputWithUnit>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import CollapseHeader from "@/components/interface/elements/base/CollapseHeader.vue";
import FormInputWithUnit from "@/components/interface/elements/base/FormInputWithUnit.vue";

export default {
  name: "CompileStrategySelect",
  components: {FormInputWithUnit, CollapseHeader},
  props: {
    strategyOptions: {type: Array, required: true},
    toggleSettings: {type: Boolean, default: true},
    showStrategySelect: {type: Boolean, default: true},
  },

  data() {
    return {
      strategyOptionSelected: null,
      showSettings: false,

      sliderOptions: {
        dotSize: 14,
        height: 5,
        min: 0,
        max: 1,
        interval: 0.01,
        duration: 0,
      }
    }
  },

  methods: {
    getStrategyData() {
      if(this.strategyOptionSelected != null)
        return this.strategyOptionSelected.getStrategyData();

      return null;
    },

    setStrategyData(data) {
      if(data == null) { // Reset
        this._onStrategySelected(this.strategyOptions[0]);
        this.strategyOptionSelected.reset();

        return;
      }

      let name = data["name"];

      for(let option of this.strategyOptions) {
        if(option.key === name) {
          option.setData(data["settings"]);

          this._onStrategySelected(option);

          return;
        }
      }
    },

    _onStrategySelected(selected) {
      this.strategyOptionSelected = selected;

      this.strategyOptionSelected.load();
    },
  },

  mounted() {
    this._onStrategySelected(this.strategyOptions[0]);
  }
}

</script>

<style>

.compileStrategySelect .optionsGrouper > i {
  right: unset !important;
  padding-left: 10px;
}

</style>

<style scoped>

.compileStrategyOptions {
  border: 1px solid var(--main-font-color);
  padding: 5px 10px;
  border-radius: 8px;
}

.compileStrategyOptions .optionSlider {
  border: initial;
  margin-top: 10px;
  height: 19px !important;
  margin-left: 7px;
  margin-right: 7px;
  box-sizing: border-box;
}

.compileStrategyOptions .optionCheckbox {
  margin-top: 0.75rem;
  margin-left: auto;
  margin-right: auto;
  display:block;
  height: 1rem;
  width: 1rem;
}

.compileStrategyOptions .optionTextInput {
  min-width: 0;
}

.compileStrategyOptions .formInputLabel {
  width: 125px;
}

.optionsContainer {
  min-height: 5px;
  max-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
  margin-top: 10px;

  margin-right: -10px;
  padding-right: 10px;
}

.optionsContainer > .formInputContainer {
  margin-top: 0;
}

.optionsContainer > .formInputContainer:not(:first-child) {
  margin-top: 10px;
}

.optionsGrouper {
  width: 100% !important;
  text-align: center;
  font-weight: bold;
}

.settingsToggle {
  position: relative;
  cursor: pointer;
  text-align: center;
  width: calc(100% + 10px);
  margin-top: 10px;
  border-top: 1px solid var(--main-font-color);
  margin-left:-5px;
  padding-top: 5px;
  text-decoration: underline;
}

</style>
