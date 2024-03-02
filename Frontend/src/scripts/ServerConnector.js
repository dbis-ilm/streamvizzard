import axios from "axios";
import {PIPELINE_STATUS, setPipelineStatus} from "@/scripts/tools/PipelineStatus";

let _instance = null;

export class ServerConnector {
    API_PATH = "http://localhost:";

    constructor(apiPort, wsPort, onReceiveCallback) {
        this.apiPort = apiPort;
        this.socketCon = null;
        this.wsPort = wsPort;

        this.onReceiveCallback = onReceiveCallback;

        _instance = this;
    }

    _assureSocket() {
        if(this.socketCon == null) {
            this.socketCon = new WebSocket("ws://localhost:" + this.wsPort)

            this.socketCon.onmessage = async (ev) => {
                await this.onReceiveCallback(JSON.parse(ev.data));
            }

            this.socketCon.onclose = function() {
                //If server closed the connection
                setPipelineStatus(PIPELINE_STATUS.STOPPED);

                _instance.socketCon = null;
            }
        }
    }

    startPipeline(data) {
        this._assureSocket();

        this.apiSend(this.API_PATH + this.apiPort + "/startPipeline", data);
    }

    stopPipeline(data) {
        this.apiSend(this.API_PATH + this.apiPort + "/stopPipeline", data);
    }

    changeHeatmapType(data) {
        this.apiSend(this.API_PATH + this.apiPort + "/changeHeatmap", data);
    }

    toggleAdvisor(data) {
        this.apiSend(this.API_PATH + this.apiPort + "/toggleAdvisor", data);
    }

    changeDebuggerState(data) {
        this.apiSend(this.API_PATH + this.apiPort + "/changeDebuggerState", data);
    }

    changeDebuggerConfig(data) {
        this.apiSend(this.API_PATH + this.apiPort + "/changeDebuggerConfig", data);
    }

    requestDebuggerStep(data) {
        this.apiSend(this.API_PATH + this.apiPort + "/requestDebuggerStep", data);
    }

    compile(pipelineData, compileData) {
        this._assureSocket();

        this.apiSend(this.API_PATH + this.apiPort + "/compile", {"pipeline": pipelineData, "compileData": compileData});
    }

    simulate(pipelineData, simulateData, startMetaData) {
        this._assureSocket();

        this.apiSend(this.API_PATH + this.apiPort + "/simulate", {"pipeline": pipelineData, "simulateData": simulateData, "meta": startMetaData});
    }

    socketSend(data) {
        this.socketCon.send(JSON.stringify(data))
    }

    apiSend(url, data) {
        axios.post(url, JSON.stringify(data)).then(() => {});
    }
}
