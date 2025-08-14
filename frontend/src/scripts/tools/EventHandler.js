export const EVENTS = {
    DISCONNECTED: 0,
    PIPELINE_STATUS_CHANGED: 1, //Param: Status
    CONNECTION_CREATED: 2, //Param: Connection
    CONNECTION_REMOVED: 3, //Param: Connection
    CONNECTION_DATA_UPDATED: 4, //Param: Data
    NODE_CREATE: 5, //Param: Node
    NODE_REMOVED: 6, //Param: Node
    CLEAR_PIPELINE: 7, //Param: Editor
    HISTORY_STATE_CHANGED: 8, //Param: State
    PIPELINE_LOADED: 9,
    NODE_PARAM_CHANGED: 10, //Param: Node, Control, OldVal
    NODE_NAME_CHANGED: 11, //Param: Node, Old
    NODE_SOCKET_NAME_CHANGED: 12, //Param: Node, Socket, Old
    GROUP_NAME_CHANGED: 13, //Param: Group, Old
    GROUP_SIZE_CHANGED: 14, //Param: Group, Old
    GROUP_COLLAPSED: 15, //Param: Group, Collapsed
    NODE_DISPLAY_CHANGED: 16, //Param: Node, Old (only for manual changes)
    DEBUG_UI_EVENT_REGISTERED: 17, // Param: Event
    UI_HISTORY_TRAVERSE: 18, // Param: traversing [bool], debugging[bool]
    MODAL_OPENED: 19, // Param: Modal Name
    COMPILE_CONF_CHANGED: 20, // Param: Node
    PIPELINE_MODIFIED: 21, // Param: PipelineUpdate, Called when any modification to the pipeline was conducted
    NODE_REPLACED: 22 // Param: Node, OldNode
}

const eventListener = new Map();

export function registerEvent(events, callback) {
    if(!Array.isArray(events)) events = [events];

    for(let event of events) {
        if(eventListener.has(event)) {
            let list = eventListener.get(event);
            list.push(callback);
        } else {
            let newList = [];
            newList.push(callback);

            eventListener.set(event, newList);
        }
    }

    return callback;
}

export function unregisterEvent(event, callback) {
    if(eventListener.has(event)) {
        let list = eventListener.get(event);

        let idx = list.indexOf(callback);
        if(idx !== -1) list.splice(idx, 1);
    }
}

export function executeEvent(event, params) {
    if(eventListener.has(event)) {
        let list = eventListener.get(event);

        if(Array.isArray(params))
            for(let elm of list) elm(...params);
        else
            for(let elm of list) elm(params);
    }
}
