<template>
  <div class="editorHistory"></div>
</template>

<script>

import {EVENTS, INTERACTION, registerEvent, unregisterEvent} from "@/scripts/tools/EventHandler";
import {
  AddOperatorAction,
  OperatorParamCA,
  OperatorNameCA,
  RemoveOperatorAction, SocketNameCA, OperatorResizeCA, OperatorChangeAction
} from "@/scripts/tools/editorHistory/OperatorAction";
import {
  AddConnectionAction,
  RemoveConnectionAction,
  RerouteChangeAction
} from "@/scripts/tools/editorHistory/ConnectionAction";
import {
  GroupChangeAction,
  GroupMoveAction,
  GroupNameChangeAction, GroupOperatorAdded, GroupOperatorRemoved,
} from "@/scripts/tools/editorHistory/GroupAction";
import {MoveAction} from "@/scripts/tools/editorHistory/MoveAction";

export default {
  props: {maxEvents: { required: true }, canUpdateEvent: {type: Function}, onEventAdded: {type: Function}, clearRedoOnNewEvent: {type: Boolean, default: true}},

  data() {
    return {
      undoEvents: [],
      redoEvents: [],

      eventRegistrationLookup: {},

      silent: false,
    }
  },

  mounted() {
    //Register all event listener

    this._registerPipeline();
    this._registerOperators();
    this._registerConnections();
    this._registerGroups();

    this._registerEventListener(EVENTS.UI_HISTORY_TRAVERSE, (traversing, debugging) => {
      this.silent = traversing;

      if(debugging) this.clear(); // When traversing, no manual history should exist
    });
  },

  beforeDestroy() {
    for(let [, v] of Object.entries(this.eventRegistrationLookup))
      unregisterEvent(v["event"], v["callback"]);

    this.eventRegistrationLookup = {};
  },

  methods: {
    _registerPipeline() {
      this._registerEventListener(EVENTS.PIPELINE_LOADED, this.clear);
      this._registerEventListener(EVENTS.PIPELINE_CLEARED, this.clear);
    },

    _registerOperators() {
      this._registerEventListener(EVENTS.OP_CREATED, (op) => { this.addEvent(new AddOperatorAction(op)) });
      this._registerEventListener(EVENTS.OP_REMOVED, (op) => { this.addEvent(new RemoveOperatorAction(op)) });

      this._registerEventListener(EVENTS.OP_PARAM_CHANGED, (op, param, oldVal) => { this.addEvent(new OperatorParamCA(op, param, oldVal)) });

      this._registerEventListener(EVENTS.OP_NAME_CHANGED, (op, oldVal) => { this.addEvent(new OperatorNameCA(op, oldVal)) });

      this._registerEventListener(EVENTS.OP_SOCKET_NAME_CHANGED, (op, socket, oldVal) => { this.addEvent(new SocketNameCA(op, socket, oldVal)) });

      // --- Change-Actions [Movement & Resize] ---

      this._registerEventListener(EVENTS.OP_INTERACTED, (op, interaction) => { this._handleDragInteraction(interaction); });

      this._registerEventListener(EVENTS.OP_MOVED, (op, prev, cascaded) => {
        if(cascaded) return; // Triggered by group movement -> skip here

        let lastElement = this.undoEvents[0];

        // All operator movements are added to same movement event
        if (lastElement instanceof MoveAction && this._canUpdateEvent(lastElement)) lastElement.update(op, prev);
        else this.addEvent(new MoveAction(op, prev));
      });

      this._registerEventListener(EVENTS.OP_RESIZED, (op, prev) => {
        let lastElement = this.undoEvents[0];

        if (lastElement instanceof OperatorResizeCA && lastElement.opID === op.id
            && this._canUpdateEvent(lastElement)) lastElement.update(op);
        else this.addEvent(new OperatorResizeCA(op, prev));
      });
    },

    _registerConnections() {
      this._registerEventListener(EVENTS.CONNECTION_CREATED, (con) => { this.addEvent(new AddConnectionAction(con)) });
      this._registerEventListener(EVENTS.CONNECTION_REMOVED, (con) => { this.addEvent(new RemoveConnectionAction(con)) });

      // Reroutes added or removed

      this._registerEventListener(EVENTS.CONNECTION_REROUTES_CHANGED, (con, prevVal) => { this.addEvent(new RerouteChangeAction(con, prevVal)); });

      // --- Change-Actions [Movement] ---

      this._registerEventListener(EVENTS.CONNECTION_REROUTES_INTERACTED, (pin, interaction) => { this._handleDragInteraction(interaction); });

      this._registerEventListener(EVENTS.CONNECTION_REROUTES_MOVED, (pin, prevVal, cascaded) => {
        if(cascaded) return; // Triggered by group movement -> skip here

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof MoveAction && this._canUpdateEvent(lastElement)) lastElement.update(pin, prevVal);
        else this.addEvent(new MoveAction(pin, prevVal));
      });
    },

    _registerGroups() {
      this._registerEventListener(EVENTS.GROUP_OP_ADDED, (g, op) => { this.addEvent(new GroupOperatorAdded(g, op)) });
      this._registerEventListener(EVENTS.GROUP_OP_REMOVED, (g, op) => { this.addEvent(new GroupOperatorRemoved(g, op)) });

      this._registerEventListener(EVENTS.GROUP_NAME_CHANGED, (group, oldVal) => { this.addEvent(new GroupNameChangeAction(group, oldVal)) });

      // --- Change-Actions [Movement] ---

      this._registerEventListener(EVENTS.GROUP_INTERACTED, (group, interaction) => { this._handleDragInteraction(interaction); });

      this._registerEventListener(EVENTS.GROUP_MOVED, (group, prevPos) => {
        let lastElement = this.undoEvents[0];

        if (lastElement instanceof GroupMoveAction && lastElement.groupID === group.id
            && this._canUpdateEvent(lastElement)) lastElement.update();
        else this.addEvent(new GroupMoveAction(group, prevPos));
      });

    },

    _handleDragInteraction(interaction) {
      // Close the last drag event when drag is finished or restarted [visual effect]

      if (!(interaction === INTERACTION.DRAG_START || interaction === INTERACTION.DRAG_END)) return;

      let lastElement = this.undoEvents[0]; // Close last change event when selecting an operator
      if (lastElement instanceof OperatorChangeAction || lastElement instanceof GroupChangeAction
          || lastElement instanceof MoveAction) lastElement.closed = true;
    },

    _registerEventListener(event, callback) {
      this.eventRegistrationLookup[event] = {"event": event, "callback": callback};

      registerEvent(event, callback);
    },

    /** @param {HistoryAction} event **/
    _canUpdateEvent(event) {

      return !this.silent && !event.closed && (this.canUpdateEvent == null || this.canUpdateEvent(event));
    },

    // --------------------------------------------------------------------

    /** @param {HistoryAction} event **/
    addEvent(event) {
      if(this.silent) return;

      this.closeLastEvent();

      if(this.onEventAdded != null) this.onEventAdded(event);

      this.undoEvents.unshift(event);

      if(this.maxEvents != null && this.undoEvents.length > this.maxEvents) this.undoEvents.pop();

      // When we add a new undo event we need to invalidate the redo events
      if(this.clearRedoOnNewEvent) this.redoEvents = [];
    },

    async performUndo(prependRedo = true) {
      if (!this.hasUndo()) return;

      this.closeLastEvent();

      let event = this.undoEvents.shift();

      this.silent = true;
      let hadEffect = await event.undo();
      if(prependRedo) this.redoEvents.unshift(event);
      this.silent = false;

      return hadEffect;
    },

    async performRedo(prependUndo = true) {
      if (!this.hasRedo()) return;

      let event = this.redoEvents.shift();

      this.silent = true;
      let hadEffect = await event.redo();
      if(prependUndo) this.undoEvents.unshift(event);
      this.silent = false;

      return hadEffect;
    },

    closeLastEvent() {
      let lastElement = this.undoEvents[0];

      if(lastElement) lastElement.closed = true;
    },

    hasUndo() {
      return this.undoEvents.length > 0;
    },

    hasRedo() {
      return this.redoEvents.length > 0;
    },

    peekNextUndo() {
      return this.hasUndo() ? this.undoEvents[0] : null;
    },

    peekNextRedo() {
      return this.hasRedo() ? this.redoEvents[0] : null;
    },

    clearRedo() {
      this.redoEvents = [];
    },

    clearUndo() {
      this.undoEvents = [];
    },

    clear() {
      this.clearRedo();
      this.clearUndo();
    },
  }
}
</script>
