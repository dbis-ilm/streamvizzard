<template>
  <div class="editorHistory"></div>
</template>

<script>
import {EVENTS, registerEvent, unregisterEvent} from "@/scripts/tools/EventHandler";
import {
  AddNodeAction,
  DragNodeAction, NodeChangeAction,
  NodeParamChangeAction,
  NodeNameChangeAction,
  RemoveNodeAction, NodeSocketNameChangeAction, NodeResizeChangeAction
} from "@/scripts/tools/editorHistory/NodeAction";
import {AddConnectionAction, RemoveConnectionAction} from "@/scripts/tools/editorHistory/ConnectionAction";
import {
  AddGroupAction,
  DragGroupAction, GroupChangeAction,
  GroupNameChangeAction, GroupSizeChangeAction,
  RemoveGroupAction
} from "@/scripts/tools/editorHistory/GroupAction";

export default {
  name: "EditorHistory",
  props: {maxEvents: { required: true }, canUpdateEvent: {type: Function}, canAddEvent: {type: Function}, clearRedoOnNewEvent: {type: Boolean, default: true}},

  data() {
    return {
      editor: null,
      undoEvents: [],
      redoEvents: [],

      eventRegistrationLookup: {},

      silent: false,
    }
  },

  beforeDestroy() {
    this.destroy();
  },

  methods: {
    initialize(editor) {
      this.editor = editor;

      //Register all event listener

      this._registerPipeline();
      this._registerNodes(editor);
      this._registerConnections(editor);
      this._registerGroups(editor);

      this._registerEventListener(EVENTS.UI_HISTORY_TRAVERSE, (traversing, debugging) => {
        this.silent = traversing;

        if(debugging) this.clear(); // When traversing, no manual history should exist
      });

      this.clear();
    },

    destroy() {
      if(this.editor == null) return;

      for(let [, v] of Object.entries(this.eventRegistrationLookup)) {
        let event = v["event"];
        let callback = v["callback"];
        let editor = v["editor"];

        if(!editor) unregisterEvent(event, callback);
        else { // .removeEventListener function available, do it manually
          let eventArray = event.split(" ");
          for(let event of eventArray) this.editor.events[event] = this.editor.events[event].filter(v => v !== callback);
        }
      }

      this.eventRegistrationLookup = {};
    },

    // --------------------------------------------------------------------

    _registerPipeline() {
      this._registerEventListener(EVENTS.PIPELINE_LOADED, this.clear);
      this._registerEventListener(EVENTS.CLEAR_PIPELINE, this.clear);
    },

    _registerNodes(editor) {
      this._registerEventListener(EVENTS.NODE_CREATE, (node) => {!this.silent ? this.addEvent(new AddNodeAction(editor, node)) : null});
      this._registerEventListener(EVENTS.NODE_REMOVED, (node) => {!this.silent ? this.addEvent(new RemoveNodeAction(editor, node)) : null});

      //No longer tracked
      //editor.on('nodeMonitorStateChanged', ({node, state}) => {!this.silent ? this.addEvent(new CollapseNodeAction(editor, node, state)) : null})

      // DRAG

      this._registerEventListener('nodetranslated', ({ node, prev }) => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof DragNodeAction && lastElement.nodeID === node.id
            && !lastElement.closed && this._canUpdateEvent(lastElement)) lastElement.update(node);

        //Only add node drag event if node is not in group that is currently dragged
        else if(!(lastElement instanceof DragGroupAction && !lastElement.closed && lastElement.getGroup().linkedTo(node)))
          this.addEvent(new DragNodeAction(editor, node, prev));
      }, true);

      this._registerEventListener('nodeselected', (node) => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        //Make sure that we start a new drag action once we (re)start dragging a node
        if (lastElement instanceof DragNodeAction && lastElement.nodeID === node.id) lastElement.closed = true;
      }, true);

      // PARAMS

      this._registerEventListener(EVENTS.NODE_PARAM_CHANGED, (node, ctrl, oldVal) => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof NodeParamChangeAction && lastElement.nodeID === node.id
            && lastElement.ctrlKey === ctrl.key && !lastElement.closed
            && this._canUpdateEvent(lastElement)) lastElement.update(node);
        else this.addEvent(new NodeParamChangeAction(editor, node, ctrl.key, oldVal));
      });

      // NAME

      this._registerEventListener(EVENTS.NODE_NAME_CHANGED, (node, oldVal) => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof NodeNameChangeAction && lastElement.nodeID === node.id
            && !lastElement.closed && this._canUpdateEvent(lastElement)) lastElement.update(node);
        else this.addEvent(new NodeNameChangeAction(editor, node, oldVal));
      })

      // SOCKET NAME

      this._registerEventListener(EVENTS.NODE_SOCKET_NAME_CHANGED, (node, socket, oldVal) => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof NodeSocketNameChangeAction && lastElement.nodeID === node.id
            && lastElement.key === socket.key && !lastElement.closed
            && this._canUpdateEvent(lastElement)) lastElement.update(socket);
        else this.addEvent(new NodeSocketNameChangeAction(editor, node, socket, oldVal));
      })

      // Resize

      this._registerEventListener('nodeResized', ({node, prev}) => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof NodeResizeChangeAction && lastElement.nodeID === node.id
            && !lastElement.closed && this._canUpdateEvent(lastElement)) lastElement.update(node);
        else this.addEvent(new NodeResizeChangeAction(editor, node, prev));
      }, true);

      // Display Change - No longer tracked
      //registerEvent(EVENTS.NODE_DISPLAY_CHANGED, (node, prev) => {!this.silent ? this.addEvent(new DisplayChangeNodeAction(editor, node, prev)) : null});

      // ALL CHANGE EVENTS

      //Mark change actions as done when node is deselected
      this._registerEventListener('nodeSelectionCleared', () => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];
        if (lastElement instanceof NodeChangeAction) lastElement.closed = true;
      }, true);
    },

    _registerConnections(editor) {
      this._registerEventListener(EVENTS.CONNECTION_CREATED, (con) => {!this.silent ? this.addEvent(new AddConnectionAction(editor, con)) : null});
      this._registerEventListener(EVENTS.CONNECTION_REMOVED, (con) => {!this.silent ? this.addEvent(new RemoveConnectionAction(editor, con)) : null});
    },

    _registerGroups(editor) {
      this._registerEventListener('commentcreated', (comment) => { !this.silent ? this.addEvent(new AddGroupAction(editor, comment)) : null}, true);
      this._registerEventListener('commentremoved', (comment) => { !this.silent ? this.addEvent(new RemoveGroupAction(editor, comment)) : null}, true);

      //registerEvent(EVENTS.GROUP_COLLAPSED, (group, state) => {!this.silent ? this.addEvent(new CollapseGroupAction(editor, group, state)) : null})

      //Name Change

      this._registerEventListener(EVENTS.GROUP_NAME_CHANGED, (comment, oldVal) => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof GroupNameChangeAction && lastElement.getGroup().getID() === comment.getID()
            && !lastElement.closed && this._canUpdateEvent(lastElement)) lastElement.update(comment);
        else this.addEvent(new GroupNameChangeAction(editor, comment, oldVal));
      });

      //Size Change

      this._registerEventListener(EVENTS.GROUP_SIZE_CHANGED, (comment, oldVal) => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof GroupSizeChangeAction && lastElement.getGroup().getID() === comment.getID()
            && !lastElement.closed && this._canUpdateEvent(lastElement)) lastElement.update(comment);
        else this.addEvent(new GroupSizeChangeAction(editor, comment, oldVal));
      });

      // Movement

      this._registerEventListener('commentMoved', ({comment, prev}) => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof DragGroupAction && lastElement.getGroup().getID() === comment.getID()
            && !lastElement.closed && this._canUpdateEvent(lastElement)) lastElement.update();
        else this.addEvent(new DragGroupAction(editor, comment, prev));
      }, true);

      //Make sure that we close prev change actions when we select a node or click anywhere
      this._registerEventListener('nodeselected click commentMoveStart', () => {
        if(this.silent) return;

        let lastElement = this.undoEvents[0];

        if (lastElement instanceof GroupChangeAction) lastElement.closed = true;
      }, true);
    },

    _registerEventListener(event, callback, editorEvent=false) {
      // Key changes datatype to string but events might be numbers aswell..
      this.eventRegistrationLookup[event] = {"event": event, "editor": editorEvent, "callback": callback};

      if(!editorEvent) registerEvent(event, callback);
      else this.editor.on(event, callback);
    },

    _canUpdateEvent(event) {
      return this.canUpdateEvent == null || this.canUpdateEvent(event);
    },

    // --------------------------------------------------------------------

    addEvent(event) {
      if(this.canAddEvent != null && !this.canAddEvent(event)) return;

      this.undoEvents.unshift(event);

      if(this.maxEvents != null && this.undoEvents.length > this.maxEvents) this.undoEvents.pop();

      //When we add a new undo event we need to invalidate the redo events
      if(this.clearRedoOnNewEvent) this.redoEvents = [];
    },

    async performUndo(prependRedo = true) {
      if (!this.hasUndo()) return;

      let event = this.undoEvents.shift();

      this.silent = true;
      await event.undo();
      if(prependRedo) this.redoEvents.unshift(event);
      this.silent = false;
    },

    async performRedo(prependUndo = true) {
      if (!this.hasRedo()) return;

      let event = this.redoEvents.shift();

      this.silent = true;
      await event.redo();
      if(prependUndo) this.undoEvents.unshift(event);
      this.silent = false;
    },

    getNextUndo() {
      if(!this.hasUndo()) return null;

      return this.undoEvents[0];
    },

    getNextRedo() {
      if(!this.hasRedo()) return null;

      return this.redoEvents[0];
    },

    hasUndo() {
      return this.undoEvents.length > 0;
    },

    hasRedo() {
      return this.redoEvents.length > 0;
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
