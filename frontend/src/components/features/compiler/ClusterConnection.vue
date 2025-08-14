<template>
  <div @mouseover="_onHover(true)" @mouseleave="_onHover(false)">
    <hr>
    <div>Connection ID: {{conID}}</div>

    <div v-if="errorMsg != null" class="errorMsg">{{errorMsg}}</div>

    <div class="formInputContainer">
      <span class="formInputLabel limitedText alignLeft" title="The connector used to send data between the clusters">Connector:&nbsp;</span>
      <v-select v-auto-blur :clearable="false" :searchable="false" :options="connectorOptions" class="formInputField" :value="connectorCfg.conType" @input="_onSelectConnectorOption($event)"></v-select>
    </div>

    <div class="formInputContainer" v-for="paramKey in (connectorCfg.params != null ? Object.keys(connectorCfg.params) : [])" :key="paramKey">
      <span class="formInputLabel limitedText alignLeft">{{ paramKey }}:&nbsp;</span>
      <input type="text" class="formInputField alignLeft" v-model="connectorCfg.params[paramKey]" @input="_onParamChange(paramKey)"/>
    </div>
  </div>
</template>

<script>

import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";
import {
  matchOtherClusterSideConType,
  matchOtherClusterSideParams
} from "@/scripts/components/compiler/CompileUtils";

export default {
  name: 'ClusterConnection',
  props: ["node", "options", "connectorCfg"],
  data() {
    return {
      connectorOptions: [],
      errorMsg: "",
    }
  },

  computed: {
    selected() {
      return this.connectorCfg.selected;
    },

    conID() {
      return this.connectorCfg["conID"]
    }
  },

  watch: {
    selected() {
      // Watch for changes in the data from server
      this._updateConnectorOptions();
    }
  },

  methods: {
    _updateConnectorOptions() {
      this.connectorOptions = [];

      let selectedFound = false;

      for(let o of this.options) {
        this.connectorOptions.push(o["ourConType"]);

        if(o["ourConType"] === this.connectorCfg["conType"]) selectedFound = true;
      }

      if(this.connectorOptions.length === 0) this.errorMsg = "No supported connectors found!";

      if(!selectedFound) {
        // Choose first option or none if no options exist
        this.connectorCfg["conType"] = this.options[0]?.["ourConType"] ?? null;
        this.connectorCfg["params"] = this.options[0]?.["ourConParams"] ?? null;
      }
    },

    _onParamChange(paramKey) {
      matchOtherClusterSideParams(this.node.id, this.conID, paramKey, this.connectorCfg["params"][paramKey]);
    },

    _onSelectConnectorOption(event) {
      for(let o of this.options) {
        if(o["ourConType"] === event) {
          this.connectorCfg["conType"] = o["ourConType"];
          this.connectorCfg["params"] = {...o["ourConParams"]};  // Copy or it will override option params on change (v-model)

          this._updateConnectorOptions();

          // Adapt other side of the cluster to select a matching connector to our new, including params

          matchOtherClusterSideConType(this.node.id, this.conID, this.connectorCfg["conType"], this.connectorCfg["params"]);

          return;
        }
      }
    },

    _onHover(over) {
      let con = PipelineService.getConnectionByID(this.conID);
      con.hover(over);
    }
  },

  mounted() {
    this._updateConnectorOptions();
  }
}

</script>

<style scoped>

hr {
  color: var(--main-border-color);
}

.formInputLabel {
  width: 110px;
}

</style>