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
}

// -------------------------------------------------------

// Set limit to avoid infinite growth in long-running pipelines (low-effort compared to time-based check)
let maxBufferSize = 100;
// How much time [s] must have passed until the next monitoring tuple is stored in the buffer
let minDeltaTime = 0.5;

export default class ConnectionMonitor {
    constructor() {
        this.throughput = 0;
        this.totalTuples = 0;
        this.time = 0;

        this.tpBuffer = [];

        // Animation properties

        this.lastTick = 0;
        this.forward = false;
        this.animationOffset = 0;
        this.animationSpeed = 0;
    }

    reset() {
        this.totalTuples = 0;
        this.tpBuffer = [];
        this.throughput = 0;
        this.time = 0;
        this.lastTick = 0;
    }

    updateData(newTp, newTupleCount, time) {
        if(this.totalTuples !== newTupleCount) {
            this.lastTick = Date.now();
            this.forward = this.totalTuples < newTupleCount;
        }

        // If we are traversing the history backwards, we remove all expired vals from buffer
        // Must rely on both, time and totalTuples, since time values are not reproducible (time of message __transfer__)

        if(newTupleCount <= this.totalTuples || time <= this.time) {
            for(let i = this.tpBuffer.length - 1; i >= 0; i--) {
                let elm = this.tpBuffer[i];

                if(elm["time"] >= time || elm["total"] >= newTupleCount) this.tpBuffer.pop();
                else break;
            }
        }

        let lastEntry = this.tpBuffer.length > 0 ? this.tpBuffer[this.tpBuffer.length - 1] : null;

        // Avoid debugging zeroes and only add entry to buffer if enough time has passed since the last one
        if(newTupleCount > 0 && (lastEntry === null || Math.abs(lastEntry.time - time) > minDeltaTime))
            this.tpBuffer.push({"time": time, "tp": newTp, "total": newTupleCount});

        if(this.tpBuffer.length > maxBufferSize) this.tpBuffer.shift();

        this.time = time;
        this.throughput = newTp;
        this.totalTuples = newTupleCount;

        // We consider 120 tup/s as the max displayed speed value [remap]
        this.animationSpeed = remap(this.throughput, 0, 120, monitorAnimationSpeed[0], monitorAnimationSpeed[1], true);
    }

    calculateAnimationOffset() {
        let current = this.animationOffset - (this.forward ? 1 : -1) * this.animationSpeed;

        if(!Number.isFinite(current)) current = 0;
        else current = Math.round(current);

        this.animationOffset = current;

        return this.animationOffset;
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
