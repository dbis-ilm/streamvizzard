import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import {clamp, debounce, safeVal, valueOr} from "@/scripts/tools/Utils";
import {getDataTypeForName} from "@/scripts/pipeline/operators/modules";
import {SvInstance} from "@/scripts/StreamVizzard";

// ----------------------------------------------------- Interface -----------------------------------------------------

export function initializeOpMonitor() {
    registerEvent(EVENTS.OP_SOCKET_COUNT_CHANGED, op => { op.monitor.onSocketsChanged()});
}

export function onOperatorDataUpdate(entry) {
    const op = SvInstance.pipeline.getOperatorByID(entry["id"]);

    if(op == null) return;

    let displayData = entry["data"];

    op.monitor.visualizeDisplayData(displayData);

    op.monitor.executionStats.addNewEntry(entry["time"], entry["exTime"], entry["dataSize"], entry["totalTuples"],
        safeVal(displayData?.["dFetch"]), displayData != null);

    SvInstance.monitor.heatmap.signalNewStats();
}

export function onOperatorMessageBrokerUpdate(entry) {
    let op = SvInstance.pipeline.getOperatorByID(entry["id"]);

    if(op == null) return;

    let broker = entry["broker"];

    op.monitor.socketDataIN = new OpBrokerStats(broker.max, broker.msg);
}

// ---------------------------------------------------------------------------------------------------------------------

// Utilized to explicitly indicate empty data sent by server [missing data]
export class EmptyMonitorData {}

// Set limit to avoid infinite growth in long-running pipelines (low-effort compared to time-based check)
let bufferMaxSize = 100;

// How much time [s] must have passed until the next monitoring tuple is stored in the buffer
let bufferMinDeltaTime = 0.5;

// After how much time [s] we consider new values to almost replace old ones in EMA calculation
let arrivalDeltaEMAWindow = 1.5;

export class OperatorMonitor {
    constructor(operator) {
        this.operator = operator;

        // Heatmap Data

        this.heatmapRating = 0;

        // Execution Stats

        this.executionStats = new OpExecutionStats(this);

        this.rawDataType = null;

        // Data Display

        this.displaySocket = 0;

        /** @type MonitorDataType **/
        this.displayDataType = null;
        /** @type MonitorDisplayMode **/
        this.displayMode = null;
        this.displayModeSettings = null;

        this.displayDataStructure = null; // Structure of data
        this.displayDataInspect = null; // Inspect command for data structure

        this.displayDataTransformer = {}; // {sockID: code}

        this.displayData = null;

        this.displayUpdateRequested = false;

        // Socket Data

        /** @type {OpBrokerStats | null} */
        this.socketDataIN = null;
    }

    // -------------------------------------------------- Data Display -------------------------------------------------

    visualizeDisplayData(data) {
        // If no data was sent, we do not update display templates
        // Happens when sendData is false OR when we just updated display mode and current data was dropped, or debugging

        if(data == null) {
            this.displayData = null;

            return;
        }

        // If we requested an displayMode update, we wait for the acknowledgment from the server
        // to avoid switching back to previous templates when receiving "outdated" data

        if(this.displayUpdateRequested) {
            if(!safeVal(data["ackUpdate"], false)) return;

            this.displayUpdateRequested = false;
        }

        this.rawDataType = data["rawType"];

        // Update display

        this.updateDisplaySocket(data["dSocket"], false);
        this.updateDisplayDataType(getDataTypeForName(data["dType"]), false);
        if(this.displayDataType != null) this.updateDisplayMode(this.displayDataType.getDisplayMode(safeVal(data["dMode"]), true), false);

        this.displayData = valueOr(data["data"], new EmptyMonitorData());

        let dataStruct = data["struct"];
        if(dataStruct == null) { // No inspection
            this.displayDataStructure = null;
            this.updateDisplayDataInspect(null, false);
        } else if(dataStruct["data"]) { // Only returns data if structure changed
            this.displayDataStructure = dataStruct["data"];
            this.updateDisplayDataInspect(dataStruct["cmd"], false); // Initially select root
        }

        // Visualize (or reset) error that occurred during data display

        let error = safeVal(data["error"])
        if(error != null) error = "Data Transformer Error:\n" + error;

        this.operator.errorMsg = error;
    }

    onSocketsChanged() {
        let socketOutCount = this.operator.outputs.length;

        // Ensure socket is in range of valid socketCount, no outSockets -> displaySocket = 0
        let socket = clamp(this.displaySocket, 0, Math.max(0, socketOutCount - 1));

        this.updateDisplaySocket(socket);
    }

    // --- Update handler ---

    updateDisplaySocket(newDisplaySocket, manual=true) {
        // DisplaySocket changed -> reset DisplayDataType & Inspect

        if(manual) {
            this.displayDataStructure = null;
            this.updateDisplayDataInspect(null, false);
        }

        if(this.displaySocket !== newDisplaySocket) {
            this.displaySocket = newDisplaySocket;

            let updateSynced = this.updateDisplayDataType(null, false); // Already triggering

            this.displayData = null;

            if(manual && !updateSynced) {
                this.requestDisplayUpdate();

                return true;
            }
        }

        return false;
    }

    updateDisplayDataType(newDt, manual=true) {
        // DataType changes -> reset DisplayMode to default

        if(newDt !== this.displayDataType) {
            this.displayDataType = newDt;

            let updateSynced;
            if(this.displayDataType == null) updateSynced = this.updateDisplayMode(null, manual);
            else updateSynced = this.updateDisplayMode(this.displayDataType.getDefaultMode(), manual);

            this.displayData = null;

            return updateSynced;
        }

        return false;
    }

    updateDisplayMode(newDm, manual=true) {
        // Display mode changes -> reset settings (to default)

        if(newDm !== this.displayMode) {
            this.displayMode = newDm;

            let updateSynced = newDm != null ? this.updateDisplayModeSettings(newDm.getSafeSettings(), false) : false;

            this.displayData = null;

            if(manual && !updateSynced) {
                this.requestDisplayUpdate();

                return true;
            }
        }

        return false;
    }

    updateDisplayModeSettings(newSettings, manual=true) {
        if(JSON.stringify(newSettings) !== JSON.stringify(this.displayModeSettings)) {
            this.displayModeSettings = newSettings;

            if(this.displayMode == null) return false;

            if(manual && this.displayMode.template.syncProps) {
                this.requestDisplayUpdate();

                return true;
            }
        }

        return false;
    }

    updateDisplayDataInspect(newInspect, manual=true) {
        if(JSON.stringify(newInspect) !== JSON.stringify(this.displayDataInspect)) {
            this.displayDataInspect = newInspect;

            if(manual) {
                this.requestDisplayUpdate();

                return true;
            }
        }

        return false;
    }

    updateDisplayDataTransformer(socket, newTf, manual=true) {
        if(newTf !== safeVal(this.displayDataTransformer[socket])) {
            this.displayDataTransformer[socket] = newTf;

            if(manual) {
                this.requestDisplayUpdate();

                return true;
            }
        }

        return false;
    }

    requestDisplayUpdate() {
        this.displayUpdateRequested = true;

        this.operator.onConfigChanged();
    }

    // ------------------------------------------------ Config / Storage -----------------------------------------------

    getDisplayConfig() {
        return {
            dataType: this.displayDataType != null ? this.displayDataType.name : null,
            socket: this.displaySocket,
            mode: this.displayMode != null ? this.displayMode.modeID : null,
            settings: this.displayModeSettings,
            inspect: this.displayDataInspect,
            transformer: safeVal(this.displayDataTransformer[this.displaySocket], null)
        };
    }

    exportSaveData() {
        return {"displayMode": this.displayMode != null ? this.displayMode.modeID : null,
                "displayDataType": this.displayDataType != null ? this.displayDataType.name : null,
                "displaySocket": this.displaySocket, "displayModeSettings": this.displayModeSettings,
                "displayDataTransformer": this.displayDataTransformer, "displayInspectCmd": this.displayDataInspect};
    }

    importSaveData(data) {
        this.updateDisplaySocket(safeVal(data["displaySocket"], this.displaySocket));
        this.updateDisplayDataType(valueOr(getDataTypeForName(safeVal(data["displayDataType"]), this.displayDataType)));

        if(this.displayDataType != null)
            this.updateDisplayMode(this.displayDataType.getDisplayMode(safeVal(data["displayMode"]), true));

        if(this.displayMode != null)
            this.updateDisplayModeSettings(valueOr(data["displayModeSettings"], this.displayModeSettings));

        this.displayDataInspect = safeVal(data["displayInspectCmd"], this.displayDataInspect);
        this.displayDataTransformer = safeVal(data["displayDataTransformer"], this.displayDataTransformer);
    }

    reset(keepDisplayData=false) {
        this.heatmapRating = 0;
        this.executionStats.reset();
        this.socketDataIN = null;
        this.displayUpdateRequested = false;

        if(!keepDisplayData) this.displayData = null;
    }
}

class OpBrokerStats {
    constructor(max, count) {
        this.max = max;
        this.count = count; // Current messages per socket
    }
}

class OpStatsEntry {
    /** @param {Number} time Timestamp of capturing
     * @param {Number} exTime Execution duration of operator
     * @param {Number} dataSize Produced output data size
     * @param {Number} totalTuples Number of processed tuples so far
     * @param {Number} displayFetchTime Duration to prepare the display data
     * @param {Number} displayRenderTime Duration to render the display data */
    constructor(time, exTime, dataSize, totalTuples, displayFetchTime, displayRenderTime) {
        this.time = time;
        this.exTime = exTime; // [ms]
        this.dataSize = dataSize; // [kB]
        this.totalTuples = totalTuples;
        this.displayFetchTime = displayFetchTime;
        this.displayRenderTime = displayRenderTime; // Only reflects first render data element
    }
}

class OpExecutionStats {
    /** @param {OperatorMonitor} monitor */
    constructor(monitor) {
        this.monitor = monitor;

        this.perfWarning = null; // If slow execution/render was detected
        this.warningComponents = [null, null, null]; // 3 types of warnings tracked individually

        // Current state in time

        this.time = 0; // = last tuple process time
        this.totalTuples = 0;

        /** @type {OpStatsEntry[]} **/
        this.entries = []; // Follows ´bufferMinDeltaTime´ to sparsely capture execution metrics

        // EMA-smoothened UI-related execution metrics

        this.entryArrivalDeltaEMA = 0; // [ms]
        this.lastRenderTime = 0;  // [s]
        this.displayRenderDurationEMA = 0; // [ms]
        this.displayFetchDurationEMA = 0; // [ms]
        this.processingTpEMA = 0 // [tup/s]

        // To avoid jumping message popups for quickly changing states
        this.debouncedWarningUpdate = debounce(() => {
            this.perfWarning = this.warningComponents.filter(Boolean).join('\n') || null;
        }, 2000);
    }

    get currentExTime() {
        let lastEntry = this.entries.at(-1);

        return lastEntry != null ? lastEntry.exTime : 0;
    }

    get currentDataSize() {
        let lastEntry = this.entries.at(-1);

        return lastEntry != null ? lastEntry.dataSize : 0;
    }

    addNewEntry(time, exTime, dataSize, totalTuples, displayFetchTime, hasDisplayData) {
        // If we are traversing the history backwards, we remove all expired vals from buffer
        // Must rely on both, time and totalTuples, since time values are not reproducible (time of message __transfer__)

        if(totalTuples <= this.totalTuples || time <= this.time) {
            for(let i = this.entries.length - 1; i >= 0; i--) {
                let elm = this.entries[i];

                if(elm.time >= time || elm.totalTuples >= totalTuples) this.entries.pop();
                else break;
            }
        }

        let lastEntry = this.entries.at(-1) || null;

        // Avoid debugging zeroes and only add entry to buffer if enough time has passed since the last one
        if(totalTuples > 0 && (lastEntry === null || Math.abs(lastEntry.time - time) > bufferMinDeltaTime)) {
            this.entries.push(new OpStatsEntry(time, exTime, dataSize / 1000, totalTuples,
                displayFetchTime, hasDisplayData  ? null : 0));
        }

        if(this.entries.length > bufferMaxSize) this.entries.shift();

        this.entryArrivalDeltaEMA = this.calculateEMA(1000 * Math.abs(time - this.time), this.entryArrivalDeltaEMA, time, this.time);
        this.displayFetchDurationEMA = this.calculateEMA(displayFetchTime, this.displayFetchDurationEMA, time, this.time);
        this.processingTpEMA = this.calculateEMA((totalTuples - this.totalTuples) / (time - this.time), this.processingTpEMA, time, this.time);

        this.time = time;
        this.totalTuples = totalTuples;

        // Analyze performance

        if(this.monitor.socketDataIN != null && this.monitor.socketDataIN.count.some(n => n >= this.monitor.socketDataIN.max))
            this.updatePerfWarning("Processing takes too much time, can't keep up with the input data rate!", 0);
        else this.updatePerfWarning(null, 0);

        if(!hasDisplayData) {
            this.updatePerfWarning(null, 1, true);
            this.updatePerfWarning(null, 2, true);
        }
    }

    updateRenderTime(renderTime) {
        // Called for each data render. However, entries are only tracked sparsely (every 0.5 s) in the buffer, so not
        // every entry has a valid render duration annotated. This is acceptable since render durations are just a
        // bonus for the user and no critical information. Moreover, render/process is sync, so the whole UI (including
        // data retrieval) slows down if render is slow. (So no tuples are dropped or buffered within the watchers).

        let bufferEntry = this.entries.at(-1);
        if(bufferEntry == null) return;

        bufferEntry.renderedEntries += 1;

        // Only apply if not already set to avoid jumping lines in the executionStats display

        if(bufferEntry.displayRenderTime == null) bufferEntry.displayRenderTime = renderTime;

        // EMA render calculation

        let currentTime = new Date().getTime();
        this.displayRenderDurationEMA = this.calculateEMA(renderTime, this.displayRenderDurationEMA, currentTime, this.lastRenderTime);
        this.lastRenderTime = currentTime;

        // Analyse render performance

        if(this.displayRenderDurationEMA > this.entryArrivalDeltaEMA)
            this.updatePerfWarning("Rendering the display data takes too much time, might slow down the UI!", 1);
        else this.updatePerfWarning(null, 1);

        if(1000 / this.displayFetchDurationEMA < this.processingTpEMA)
            this.updatePerfWarning("Fetching the display data takes too much time, might slow down pipeline!", 2);
        else this.updatePerfWarning(null, 2);
    }

    /** @param {string|null} warning
     * @param {number} type
     * @param {boolean} instant */
    updatePerfWarning(warning, type, instant= false) {
        if(warning == null) {
            if(this.warningComponents[type] == null) return; // Already empty
            this.warningComponents[type] = null;

            if(instant) this.perfWarning = this.warningComponents.filter(Boolean).join('\n') || null;
            else if(!this.debouncedWarningUpdate.isPending()) this.debouncedWarningUpdate(); // Debounce "reduce" to avoid jumps in potentially frequent show/hide
        } else {
            if(this.warningComponents[type] === warning) return; // Already set

            this.debouncedWarningUpdate.cancel();
            this.warningComponents[type] = warning;
            this.perfWarning = this.warningComponents.filter(Boolean).join('\n') || null;
        }
    }

    calculateEMA(newValue, prevEMA, newTime, lastTime) {
        if(lastTime !== 0) {
            let dt = Math.abs(newTime - lastTime); // Could be negative for debugging
            let emaAlpha = 1 - Math.exp(-dt / arrivalDeltaEMAWindow);

            // No prev EMA, just use current val to avoid reduction of current val
            if(prevEMA !== 0) return emaAlpha * newValue + (1 - emaAlpha) * prevEMA;
            else return newValue;
        }

        return 0;
    }

    reset() {
        this.perfWarning = null;
        this.warningComponents = [null, null, null];

        this.time = 0;
        this.totalTuples = 0;

        this.entryArrivalDeltaEMA = 0;
        this.displayRenderDurationEMA = 0;
        this.displayFetchDurationEMA = 0;
        this.processingTpEMA = 0;
        this.lastRenderTime = 0;

        this.entries = [];
    }
}
