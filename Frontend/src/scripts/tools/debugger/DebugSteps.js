export const DEBUG_STEPS = {
    ON_TUPLE_TRANSMITTED: "Tuple Transmitted",
    ON_TUPLE_PROCESSED: "Tuple Processed",
    PRE_TUPLE_PROCESSED: "Process Tuple",
    ON_STREAM_PROCESS_TUPLE: "Process Stream",
    ON_SOURCE_PRODUCED_TUPLE: "Tuple Produced",
    ON_OP_EXECUTED: "Executed"
}

export function getStepDescriptionForType(t) {
    for(let e in DEBUG_STEPS) {
        if(e === t) return DEBUG_STEPS[e];
    }

    return t;
}

export function getDropdownData() {
    let data = [];

    for(let e in DEBUG_STEPS) {
        data.push({"title": DEBUG_STEPS[e], "key": e})
    }

    return data;
}
