export const EVENTS = {
    DISCONNECTED: "DISCONNECTED",

    CONNECTION_CREATED: "CONNECTION_CREATED", // Param: Connection
    CONNECTION_REMOVED: "CONNECTION_REMOVED", // Param: Connection
    CONNECTION_REROUTES_CHANGED: "CONNECTION_REROUTES_CHANGED", // Param: Connection, Prev, Cascaded [bool] | Cascaded: triggered by group

    OP_CREATED: "OP_CREATED", // Param: Operator
    OP_REMOVED: "OP_REMOVED", // Param: Operator
    OP_PARAM_CHANGED: "OP_PARAM_CHANGED", // Param: Operator, Param, OldVal
    OP_NAME_CHANGED: "OP_NAME_CHANGED", // Param: Operator, Old
    OP_SOCKET_NAME_CHANGED: "OP_SOCKET_NAME_CHANGED", // Param: Operator, Socket, Old
    OP_SOCKET_COUNT_CHANGED: "OP_SOCKET_COUNT_CHANGED", // Param: Operator
    OP_RESIZED: "OP_RESIZED", // Param: Operator, PrevResizeData | Manually resized operator
    OP_SIZE_CHANGED: "OP_SIZE_CHANGED", // Param: Operator | Called everytime the operator object changes its size
    OP_MOVED: "OP_MOVED", // Param: Operator, OldPos {x,y}, Cascaded [bool] | Cascaded: triggered by group
    OP_INTERACTED: "OP_INTERACTED", // Param: Operator, Type [INTERACTION] | User interaction

    GROUP_OP_ADDED: "GROUP_OP_ADDED", // Param: Group, Operator
    GROUP_OP_REMOVED: "GROUP_OP_REMOVED", // Param: Group, Operator
    GROUP_NAME_CHANGED: "GROUP_NAME_CHANGED", // Param: Group, Old
    GROUP_MOVED: "GROUP_MOVED", // Param: Group, OldPos
    GROUP_INTERACTED: "GROUP_INTERACTED", // Param: Group, Type [INTERACTION] | User interaction

    PIPELINE_STATUS_CHANGED: "PIPELINE_STATUS_CHANGED", // Param: Status
    PIPELINE_CLEARED: "PIPELINE_CLEARED",
    PIPELINE_LOADED: "PIPELINE_LOADED",
    PIPELINE_MODIFIED: "PIPELINE_MODIFIED", // Param: PipelineUpdate, Called when any modification to the pipeline was conducted

    DEBUG_UI_EVENT_REGISTERED: "DEBUG_UI_EVENT_REGISTERED", // Param: Event
    UI_HISTORY_TRAVERSE: "UI_HISTORY_TRAVERSE", // Param: traversing [bool], debugging[bool]
    MODAL_OPENED: "MODAL_OPENED", // Param: Modal Name
}

export const INTERACTION = {
    DRAG_START: "DRAG_START", // = selected
    DRAGGING: "DRAGGING",
    DRAG_END: "DRAG_END",
}

const eventListener = new Map();

export function registerEvent(events, callback, order = 10) {
    // The order of callback execution follows the given order, starting at 0

    if(!Array.isArray(events)) events = [events];

    for(let event of events) {
        if(eventListener.has(event)) {
            let list = eventListener.get(event);
            list.push({"callback": callback, "order": order});

            list.sort((a, b) => a.order - b.order); // Assure ASC ordering according to priority

        } else {
            let newList = [];
            newList.push({"callback": callback, "order": order});

            eventListener.set(event, newList);
        }
    }

    return callback;
}

export function unregisterEvent(events, callback) {
    if(!Array.isArray(events)) events = [events];

    for(let event of events) {
        if(eventListener.has(event)) {
            let list = eventListener.get(event);

            // All entries with callback are removed

            for(let i = list.length - 1; i >= 0; i--) {
                if(list[i]["callback"] === callback) list.splice(i, 1);
            }
        }
    }
}

export function executeEvent(event, params) {
    if(eventListener.has(event)) {
        let list = eventListener.get(event);

        if(Array.isArray(params))
            for(let elm of list) elm["callback"](...params);
        else
            for(let elm of list) elm["callback"](params);
    }
}
