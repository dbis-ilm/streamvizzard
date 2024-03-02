<template>
  <modal ref="modal" name="CompilePipelineModal" transition="pop-out" :width="200" height="auto" :shiftY="0" :shiftX="0.075" style="top: 10%;">
    <div style="padding:10px;">
      <div style="text-decoration: underline;"><b>Compile Pipeline</b></div>

      <br/>

      <div>Compile Target</div>
      <v-select :options="options" label="title" :value="target" :clearable="false" :searchable="false" @input="_onChange($event)"></v-select>

      <br/>

      <div>Compile Flags</div>
      <div title="Separate multiple by comma"><input type="text" placeholder="Unset" v-model="flags" style="width: 95%;"></div>

      <div style="display:inline-block; margin-top:10px;">
        <button style="display:inline; margin:4px;" @click="hide">Close</button>
        <button style="display:inline; margin:4px;" @click="_confirm">Compile</button>
      </div>
    </div>
  </modal>
</template>

<script>

import {registerDataExporter, sendPipelineCompile} from "@/components/Main";
import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";

export default {
  name: 'CompilePipelineModal',

  data() {
    return {
      options: [{'title': 'Python Internal', 'key': 'pythonInternal'}],
      target: null,
      flags: null
    }
  },

  methods: {
    show () {
      this.$modal.show('CompilePipelineModal');
    },

    hide () {
      this.$modal.hide('CompilePipelineModal');
    },

    _confirm() {
      let tags = [];

      //Parse Tags
      if(this.flags != null) {
        let t = this.flags.trim().split(",");

        for(let st of t) {
          st = st.trim();

          if(st.length > 0) tags.push(st);
        }
      }

      sendPipelineCompile({"target": this.target.key, "flags": tags});

      this.hide();
    },

    _onChange(e) {
      this.target = e;
    },

    reset() {
      this.target = this.options[0];
      this.flags = null;
    },

    // EXPORT INTERFACE

    _getSaveData() {
      return {"target": this.target.key, "flags": this.flags}
    },

    _loadSaveData(saveData) {
      this.flags = saveData.flags;
      this.target = this.options.find(el => el.key === saveData.target) || this.options[0];
    }
  },

  mounted() {
    this.reset();

    registerDataExporter("compileData", this._getSaveData, this._loadSaveData);

    registerEvent(EVENTS.CLEAR_PIPELINE, this.reset);
  }
}
</script>
