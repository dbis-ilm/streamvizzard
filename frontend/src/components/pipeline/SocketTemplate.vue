<template>
  <div :class="['socket', socket.input ? 'input' : 'output']">
    <div v-if="socket.input" class="bubble" ref="bubble" :title="'Socket: ' + socket.id + '\n' + tooltipMessage" :style="style" @pointerdown="_onPointerDown" @pointerup="_onPointerUp"></div>
    <input ref="input" type="text" :value="socket.name" @change="_onSocketNameChange($event)"
           v-on:keyup.enter="_onNameSubmit($event)" class="socketInput editorInput limitedText editorNameInput">
    <div v-if="!socket.input" class="bubble" ref="bubble" :title="'Socket: ' + socket.id + '\n' + tooltipMessage" :style="style" @pointerdown="_onPointerDown" @pointerup="_onPointerUp"></div>
  </div>
</template>

<script>
import {clamp, makeNameInput} from "@/scripts/tools/Utils";
import $ from "jquery";
import SvSocket from "@/scripts/pipeline/SvSocket";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";

export default {
  props: {
    socket: {
      type: SvSocket, required: true
    }
  },

  data() {
    return {
      tooltipMessage: "",
      style: ""
    }
  },

  computed: {
    socketData() {
      if(!this.socket.input) return null; // Only receive IN socket data
      return this.socket.operator.monitor.socketDataIN;
    }
  },

  watch: {
    socketData() {
      let msg = 0;
      let max = 0;

      if(this.socketData != null) {
        max = this.socketData.max;
        msg = this.socketData.count.at(this.socket.id) || 0;
      }

      if(msg > 0) {
        this.tooltipMessage = "Buffer: " + msg + " Tuples";
        this.style = "transform: scale(" + (1 + clamp((msg / max), 0, 1) * 0.5) + ");";

        if(msg >= max) this.style += " border: 2px solid red;";
      } else {
        this.tooltipMessage = "";
        this.style = "";
      }
    }
  },

  methods: {
    _onSocketNameChange: function(event) {
      let prevValue = this.socket.name;

      this.socket.name = event.target.value.trim();

      if(this.socket.name.length === 0) this.socket.name = this.socket.getDefaultName();

      executeEvent(EVENTS.OP_SOCKET_NAME_CHANGED, [this.socket.operator, this.socket, prevValue]);
    },

    _onNameSubmit: function(event) {
      $(event.target).blur();
    },

    _onPointerDown(e) {
      e.stopPropagation();

      this.$streamvizzard.editor.pickSocketConnection(this.socket);
    },

    _onPointerUp(e) {
      e.stopPropagation();

      this.$streamvizzard.editor.unpickSocketConnection(this.socket);
    }
  },

  mounted() {
    makeNameInput($(this.$refs.input), $(this.$el));

    this.socket.viewConnector.connect((identifier) => {
      if(identifier === "dimensions") return this.$refs.bubble.getBoundingClientRect();
    });
  }
}
</script>

<style scoped>

.socket.input, .socket.input .socketInput {
  text-align: left;
}

.socket.output, .socket.output .socketInput {
  text-align: right;
}

.bubble {
  display: inline-block;
  cursor: pointer;
  border: 2px solid #828282;
  border-radius: 12px;
  width: 24px;
  height: 24px;
  margin: 6px;
  vertical-align: middle;
  background: #96b38a;
  box-sizing: border-box;
}

.bubble:hover {
  border-width: 4px;
}

.socket.output .bubble  {
  margin-right: -12px;
}

.socket.input .bubble {
  margin-left: -12px;
}

.socketInput {
  color: white;
  vertical-align: middle;
  display: inline-block;
  font-size: 16px;
  line-height: 24px;
  padding-top:0 !important;
  padding-bottom:0 !important;
  width: calc(100% - 28px);
}

</style>
