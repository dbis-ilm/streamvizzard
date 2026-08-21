import {remap} from "@/scripts/tools/Utils";
import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import {PIPELINE_STATUS} from "@/scripts/pipeline/Pipeline";
import {SvInstance} from "@/scripts/StreamVizzard";

// ---------------------- INTERFACE ----------------------

export function initializeConnectionMonitor() {
    registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, (status) => {
        if(status === PIPELINE_STATUS.STARTING) reset();
        else if(status === PIPELINE_STATUS.STARTED) setupMonitorAnimation();
        else if(status === PIPELINE_STATUS.STOPPED) stopMonitorAnimation();
    });
}

export function onConnectionDataUpdate(entry) {
    const conID = entry.id;

    const con = SvInstance.pipeline.getConnectionByID(conID);
    if(con == null) return;

    con.monitor.updateData(entry.tp, entry.total, entry.time);

    SvInstance.monitor.heatmap.signalNewStats();
}

// -------------------------------------------------------

// Set limit to avoid infinite growth in long-running pipelines (low-effort compared to time-based check)
let maxBufferSize = 100;
// How much time [s] must have passed until the next monitoring tuple is stored in the buffer
let minDeltaTime = 0.5;

export default class ConnectionMonitor {
    constructor() {
        // Execution Stats

        this.executionStats = new ConExecutionStats();

        // Animation Properties

        this.lastTick = 0;
        this.forward = false;
        this.animationOffset = 0;
        this.animationSpeed = 0;
    }

    reset() {
        this.lastTick = 0;
        this.executionStats.reset();
    }

    updateData(newTp, newTupleCount, time) {
        if(this.executionStats.totalTuples !== newTupleCount) {
            this.lastTick = Date.now();
            this.forward = this.executionStats.totalTuples < newTupleCount;
        }

        this.executionStats.addNewEntry(newTp, newTupleCount, time);

        // We consider 120 tup/s as the max displayed speed value [remap]
        this.animationSpeed = remap(newTp, 0, 120, monitorAnimationSpeed[0], monitorAnimationSpeed[1], true);
    }

    calculateAnimationOffset() {
        let current = this.animationOffset - (this.forward ? 1 : -1) * this.animationSpeed;

        if(!Number.isFinite(current)) current = 0;
        else current = Math.round(current);

        this.animationOffset = current;

        return this.animationOffset;
    }
}

class ConStatsEntry {
    /** @param {Number} time Timestamp of capturing
     * @param {Number} totalTuples Total tuples transmitted
     * @param {Number} throughput Current connection throughput */
    constructor(time, totalTuples, throughput) {
        this.time = time;
        this.totalTuples = totalTuples;
        this.throughput = throughput;
    }
}

class ConExecutionStats {
    constructor() {
        // Current state in time
        this.time = 0;
        this.totalTuples = 0;

        /** @type {ConStatsEntry[]} **/
        this.entries = [];
    }

    get currentThroughput() {
        let lastEntry = this.entries.at(-1);

        return lastEntry != null ? lastEntry.throughput : 0;
    }

    addNewEntry(newTp, newTupleCount, time) {
        // If we are traversing the history backwards, we remove all expired vals from buffer
        // Must rely on both, time and totalTuples, since time values are not reproducible (time of message __transfer__)

        if(newTupleCount <= this.totalTuples || time <= this.time) {
            for(let i = this.entries.length - 1; i >= 0; i--) {
                let elm = this.entries[i];

                if(elm.time >= time || elm.totalTuples >= newTupleCount) this.entries.pop();
                else break;
            }
        }

        let lastEntry = this.entries.length > 0 ? this.entries[this.entries.length - 1] : null;

        // Avoid debugging zeroes and only add entry to buffer if enough time has passed since the last one
        if(newTupleCount > 0 && (lastEntry === null || Math.abs(lastEntry.time - time) > minDeltaTime)) {
            this.entries.push(new ConStatsEntry(time, newTupleCount, newTp));
        }

        if(this.entries.length > maxBufferSize) this.entries.shift();

        this.time = time;
        this.totalTuples = newTupleCount;
    }

    reset() {
        this.time = 0;
        this.totalTuples = 0;

        this.entries = [];
    }
}

function reset() {
    for(let k of SvInstance.pipeline.connections) k.monitor.reset();
}

// ---------------------------- Animated Connections ----------------------------

const monitorAnimationSpeed = [2, 12]; //How fast the dots are moving (at min/max)
const monitorAnimationRate = 33; //In which ms interval the dots are moved (30fps)

const monitorConAnimationTickDuration = 500; // How many ms the animation will be played before a new tuple must arrive

let monitorAnimator = null;

function setupMonitorAnimation() {
    monitorAnimator = setInterval( function() {
        let now = Date.now();

        //Perform the animation of each connection if it's "active"
        for(let connection of SvInstance.pipeline.connections) {
            //If we did not receive a recent tick, we don't animate this connection
            if(now >= connection.monitor.lastTick + monitorConAnimationTickDuration) continue;

            connection.strokeDashOffset = "" + connection.monitor.calculateAnimationOffset();
        }
    }, monitorAnimationRate);
}

function stopMonitorAnimation() {
    if(monitorAnimator != null) clearInterval(monitorAnimator);
    monitorAnimator = null;
}
