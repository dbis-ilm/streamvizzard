import {EVENTS, registerEvent} from "@/scripts/tools/EventHandler";
import {clamp, safeVal, valueOr} from "@/scripts/tools/Utils";
import {getDataTypeForName} from "@/scripts/pipeline/operators/modules";
import {SvInstance} from "@/scripts/StreamVizzard";

// ----------------------------------------------------- Interface -----------------------------------------------------

export function initializeOpMonitor() {
    registerEvent(EVENTS.OP_SOCKET_COUNT_CHANGED, op => { op.monitor.onSocketsChanged()});
}

export function onOperatorDataUpdate(entry) {
    const op = SvInstance.pipeline.getOperatorByID(entry["id"]);

    if(op == null) return;

    op.monitor.visualizeDisplayData(entry["data"]);

    op.monitor.updateStats(entry["time"], entry["exTime"], entry["dataSize"], entry["totalTuples"]);
}

export function onOperatorHeatmapUpdate(entry) {
    let op = SvInstance.pipeline.getOperatorByID(entry["op"]);

    if(op == null) return;

    op.monitor.heatmapRating = entry["rating"];
}

export function onOperatorMessageBrokerUpdate(entry) {
    let op = SvInstance.pipeline.getOperatorByID(entry["id"]);

    if(op == null) return;

    let broker = entry["broker"];

    if(broker == null) {
        op.monitor.socketDataIN = null;
    } else {
        op.monitor.socketDataIN = {"max": broker.max, "count": broker.msg};
    }
}

// ---------------------------------------------------------------------------------------------------------------------

// Set limit to avoid infinite growth in long-running pipelines (low-effort compared to time-based check)
let bufferMaxSize = 100;

// How much time [s] must have passed until the next monitoring tuple is stored in the buffer
let bufferMinDeltaTime = 0.5;

export class OperatorMonitor {
    constructor(operator) {
        this.operator = operator;

        // Heatmap Data

        this.heatmapRating = 0;

        // Execution Stats

        this.time = 0;
        this.totalTuples = 0;
        this.dataSize = 0; // [bytes]
        this.exTime = 0; // [ms]

        this.statsBuffer = [];

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

        this.socketDataIN = null;  // {"max", "count": ["countSock0", "countSock1"]}
    }

    updateStats(time, exTime, dataSize, totalTuples) {
        // If we are traversing the history backwards, we remove all expired vals from buffer
        // Must rely on both, time and totalTuples, since time values are not reproducible (time of message __transfer__)

        if(totalTuples <= this.totalTuples || time <= this.time) {
            for(let i = this.statsBuffer.length - 1; i >= 0; i--) {
                let elm = this.statsBuffer[i];

                if(elm["time"] >= time || elm["total"] >= totalTuples) this.statsBuffer.pop();
                else break;
            }
        }

        let lastEntry = this.statsBuffer.length > 0 ? this.statsBuffer[this.statsBuffer.length - 1] : null;

        // Avoid debugging zeroes and only add entry to buffer if enough time has passed since the last one
        if(totalTuples > 0 && (lastEntry === null || Math.abs(lastEntry.time - time) > bufferMinDeltaTime))
            this.statsBuffer.push({"time": time, "exTime": exTime, "dataSize": dataSize, "total": totalTuples});

        if(this.statsBuffer.length > bufferMaxSize) this.statsBuffer.shift();

        this.time = time;
        this.exTime = exTime;
        this.dataSize = dataSize;
        this.totalTuples = totalTuples;
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

        // Update display

        this.updateDisplaySocket(data["dSocket"], false);
        this.updateDisplayDataType(getDataTypeForName(data["dType"]), false);
        if(this.displayDataType != null) this.updateDisplayMode(this.displayDataType.getDisplayMode(data["dMode"], true), false);

        this.displayData = data["data"];

        // Data structure is only sent when changed, otherwise contains empty obj {} -> use cached values in this case

        let dataStruct = data["struct"];
        if(dataStruct == null) {
            this.displayDataStructure = null;
            this.updateDisplayDataInspect(null, false);
        } else if(Object.keys(dataStruct).length !== 0) {
            this.displayDataStructure = dataStruct;
            this.updateDisplayDataInspect(null, false);
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
        // Display mode changes -> reset settings

        if(newDm !== this.displayMode) {
            this.displayMode = newDm;

            let updateSynced = this.updateDisplayModeSettings(null, false);

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
                "displayDataTransformer": this.displayDataTransformer};
    }

    importSaveData(data) {
        this.updateDisplaySocket(safeVal(data["displaySocket"], this.displaySocket));
        this.updateDisplayDataType(valueOr(getDataTypeForName(safeVal(data["displayDataType"]), this.displayDataType)));

        if(this.displayDataType != null)
            this.updateDisplayMode(this.displayDataType.getDisplayMode(safeVal(data["displayMode"]), true));

        if(this.displayMode != null)
            this.updateDisplayModeSettings(valueOr(data["displayModeSettings"], this.displayModeSettings));

        this.displayDataTransformer = safeVal(data["displayDataTransformer"], this.displayDataTransformer);
    }

    reset(keepDisplayData=false) {
        this.heatmapRating = 0;
        this.statsBuffer = [];
        this.time = 0;
        this.totalTuples = 0;
        this.dataSize = 0;
        this.exTime = 0;
        this.socketDataIN = null;

        this.displayUpdateRequested = false;

        if(!keepDisplayData) this.displayData = null;
    }
}
