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

export class DebugStep {
    /** @param {Number} branchID
     * @param {Number} stepID
     * @param {Number} opID
     * @param {String} type
     * @param {Number} stepTime**/
    constructor(branchID, stepID, opID, type, stepTime) {
        this.branchID = branchID;
        this.stepID = stepID;
        this.opID = opID;
        this.type = type;
        this.stepTime = stepTime;
    }
}

export class DebugStepExecution {
    /** @param {DebugStep} step
     * @param {Boolean|null} undo **/
    constructor(step, undo) {
        this.step = step;
        this.undo = undo; // null=normal execution, no undo/redo
    }
}
