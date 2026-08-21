import {SvInstance} from "@/scripts/StreamVizzard";
import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import {PIPELINE_STATUS} from "@/scripts/pipeline/Pipeline";

// Calculates adaptive buckets based on changing operator metrics

export class Heatmap {
    constructor() {
        this.type = 0;  // @type {HEATMAP}

        this.min = 0;
        this.max = 0;
        this.steps = [];

        // Calculation

        this.updateInterval = null;
        this.hasStatsUpdate = false;

        registerEvent(EVENTS.PIPELINE_CLEARED, () => { this.reset(); });

        // This client time-based approach will lead to minor differences during debugging traversal
        registerEvent(EVENTS.PIPELINE_STATUS_CHANGED, (status) => {
            if(status === PIPELINE_STATUS.STARTED) {
                this.reset();

                if(this.updateInterval == null) this.updateInterval = setInterval(() => { this.calculate(); }, 500);
            } else if(status === PIPELINE_STATUS.STOPPED) {
                if(this.updateInterval != null) clearInterval(this.updateInterval);
                this.updateInterval = null;
            }
        });
    }

    calculate() {
        if(!this.hasStatsUpdate || !this.isActive()) return;
        this.hasStatsUpdate = false;

        // Build target metrics array

        let targetMetrics = [];
        let idx = [];

        this.min = Infinity;
        this.max = 0;
        this.steps = [];

        for(let i = 0; i < SvInstance.pipeline.operators.length; i++) {
            let op = SvInstance.pipeline.operators[i];
            op.monitor.heatmapRating = 0;

            let metric = 0;

            if(this.type === HEATMAP.EXECUTION_TIME) {
                if(op.definition.source) metric = 0;  // Sources have no reasonable ExTime
                else metric = op.monitor.executionStats.currentExTime;
            }
            else if(this.type === HEATMAP.DATA_SIZE) metric = op.monitor.executionStats.currentDataSize;
            else if(this.type === HEATMAP.DISPLAY_FETCH_TIME) {
                if(!op.showData) metric = 0;  // No display data
                metric = op.monitor.executionStats.displayFetchDurationEMA;
            }
            else if(this.type === HEATMAP.DISPLAY_RENDER_TIME) {
                if(!op.showData) metric = 0;  // No display data
                metric = op.monitor.executionStats.displayRenderDurationEMA;
            }
            else if(this.type === HEATMAP.THROUGHPUT) {
                let totalTp = 0;
                let conCount = 0;

                for(let con of op.getAllConnections(false, true)) {
                    conCount++;
                    totalTp += con.monitor.executionStats.currentThroughput;
                }

                metric = conCount > 0 ? totalTp / conCount : 0;
            }

            targetMetrics.push(metric);
            idx.push(i);

            if (metric > this.max) this.max = metric;
            if (metric < this.min) this.min = metric;
        }

        let count = targetMetrics.length;

        if(count === 0 || this.min === this.max) return;

        // Calculate buckets

        this._fastInsertionSort(targetMetrics, idx);

        let buckets = new Uint16Array(count); // Give upper border of bucket (exclusive)
        let uniqueBucketCount = 0;

        // Build buckets (unique values)

        let i = 0;

        while (i < count) {
            const v = targetMetrics[i];

            // Iterate forward to find matching values (array is sorted)
            while (i + 1 < count && targetMetrics[i + 1] === v) i++;

            buckets[uniqueBucketCount++] = i + 1;

            i++;
        }

        // Merge elements from different buckets until we fulfill the bucket amount constraint

        const maxBuckets = 5;
        const totalDist = this.max - this.min;
        const invTotal = 1 / totalDist;

        while (uniqueBucketCount > maxBuckets) {
            // Find bucket to merge next element into (most small difference in value)

            let mergeID = 0;
            let smallest = Infinity;

            for (let b = 0; b < uniqueBucketCount - 1; b++) {
                const right = buckets[b] - 1;
                const next = buckets[b];
                const d = (targetMetrics[next] - targetMetrics[right]) * invTotal;

                if (d < smallest) {
                    smallest = d;
                    mergeID = b;
                }
            }

            // Merge bucket with next val

            buckets[mergeID]++;

            // Indicate empty buckets to be removed

            if (buckets[mergeID] >= buckets[mergeID + 1]) {
                for (let k = mergeID + 1; k < uniqueBucketCount - 1; k++) {
                    buckets[k] = buckets[k + 1];
                }

                uniqueBucketCount--;
            }
        }

        // Calculate value of each bucket

        const borderWith = 0.075;
        const totalAvail = 1 - (uniqueBucketCount - 1) * borderWith;

        let bucketRankings = new Float32Array(uniqueBucketCount);

        for (let b = 0; b < uniqueBucketCount; b++) {
            const end = buckets[b];
            const start = b > 0 ? buckets[b - 1] - 1 : 0; // Value dist from end [incl] of last bucket to end of our

            const range = targetMetrics[end - 1] - targetMetrics[start];
            bucketRankings[b] = range * invTotal * totalAvail;
        }

        // Finally, assign real ratings for each operator

        let total = 0;

        for (let b = 0; b < uniqueBucketCount; b++) {
            const end = buckets[b];

            const bucketR = bucketRankings[b];

            if (b < uniqueBucketCount - 1) {
                this.steps.push([
                    targetMetrics[end - 1],
                    total + bucketR + borderWith
                ]);
            }

            const start = b > 0 ? buckets[b - 1] : 0;
            const range = targetMetrics[end - 1] - targetMetrics[start]; // Range within bucket
            let prev = targetMetrics[start];

            for (let j = start; j < end; j++) {
                const v = targetMetrics[j];
                const rank = range > 0 ? (v - prev) / range : 1;
                prev = v;

                SvInstance.pipeline.operators[idx[j]].monitor.heatmapRating = total + bucketR * rank;
            }

            total += bucketR + borderWith;
        }
    }

    _fastInsertionSort(vals, idx) {
        const n = vals.length;

        for (let i = 1; i < n; i++) {
            const v = vals[i];
            const id = idx[i];
            if (v >= vals[i - 1]) continue; // Early out
            let j = i - 1;
            while (j >= 0 && vals[j] > v) {
                vals[j + 1] = vals[j];
                idx[j + 1] = idx[j];
                j--;
            }
            vals[j + 1] = v;
            idx[j + 1] = id;
        }
    }

    signalNewStats() {
        this.hasStatsUpdate = true;
    }

    show(type, resetOnSwitch=true) {
        // Reset data if type was switched (and desired)

        if(type !== this.type && resetOnSwitch) this.reset();

        this.type = type;
    }

    isActive() {
        return this.type !== 0;
    }

    isExStats () {
        return this.type > 0;
    }

    toggleExStats() {
        if(this.isExStats()) this.show(HEATMAP.NONE);
        else this.show(HEATMAP.EXECUTION_TIME);
    }

    reset() {
        this.min = 0;
        this.max = 0;
        this.steps = [];

        for(let op of SvInstance.pipeline.operators) op.monitor.heatmapRating = 0;

        this.hasStatsUpdate = false;
    }
}

export const HEATMAP = {
    COMPILE: -1,
    NONE: 0,
    EXECUTION_TIME: 1,
    DATA_SIZE: 2,
    THROUGHPUT: 3,
    DISPLAY_FETCH_TIME: 4,
    DISPLAY_RENDER_TIME: 5,
}
