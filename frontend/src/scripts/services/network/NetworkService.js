import axios from "axios";
import {registerDebuggerCMDs} from "@/scripts/services/network/commands/DebuggerCmds";
import {registerMonitorCMDs} from "@/scripts/services/network/commands/MonitorCmds";
import {registerPipelineCMDs} from "@/scripts/services/network/commands/PipelineCmds";
import {PIPELINE_STATUS} from "@/scripts/pipeline/Pipeline";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import {Service} from "@/scripts/services/Service";
import {Services} from "@/scripts/services/Services";
import {SvInstance} from "@/scripts/StreamVizzard";

const API_PATH = "http://localhost:8000";
const SOCKET_PATH = "ws://localhost:8001";


export class NetworkService extends Service {
    constructor() {
        super("NetworkService");

        this.socketCon = null;

        this.commands = new Map();
    }

    onInitialize() {
        super.onInitialize();

        registerDebuggerCMDs(this);
        registerMonitorCMDs(this);
        registerPipelineCMDs(this);
    }

    registerCommand(command) {
        this.commands.set(command.name, command);
    }

    async executeCommand(cmd, data) {
        let command = this.commands.get(cmd);

        if(command != null) await command.handleCommand(data);
    }

    _assureSocket() {
        if(this.socketCon == null) {
            this.socketCon = new WebSocket(SOCKET_PATH)

            this.socketCon.onmessage = async (ev) => {
                let data = JSON.parse(ev.data);

                await this.executeCommand(data["cmd"], data);
            }

            this.socketCon.onclose = function() {
                //If server closed the connection
                Services.Network.socketCon = null;

                SvInstance.pipeline.setPipelineStatus(PIPELINE_STATUS.STOPPED);

                executeEvent(EVENTS.DISCONNECTED);
            }
        }
    }

    async startPipeline(runtimeConfig) {
        this._assureSocket();

        return await this.apiSend(API_PATH + "/startPipeline", runtimeConfig).then();
    }

    stopPipeline() {
        this.apiSend(API_PATH + "/stopPipeline", "").then();
    }

    changeMonitorConfig(data) {
        this.apiSend(API_PATH + "/changeMonitorConfig", data).then();
    }

    changeAdvisorConfig(data) {
        this.apiSend(API_PATH + "/changeAdvisorConfig", data).then();
    }

    changeDebuggerState(data) {
        this.apiSend(API_PATH + "/changeDebuggerState", data).then();
    }

    changeDebuggerConfig(data) {
        this.apiSend(API_PATH + "/changeDebuggerConfig", data).then();
    }

    executeProvenanceQuery(data) {
        this.apiSend(API_PATH + "/executeProvenanceQuery", data).then();
    }

    async requestDebuggerStep(data) {
        return await this.apiSend(API_PATH + "/requestDebuggerStep", data);
    }

    // ---------- Pipeline Configuration Storage ----------

    async listStoredPipelines() {
        return await this.apiSend(API_PATH + "/listStoredPipelines")
    }

    async requestStoredPipeline(pipelineName) {
        return await this.apiSend(API_PATH + "/requestStoredPipeline", pipelineName)
    }

    async deleteStoredPipeline(pipelineName) {
        return await this.apiSend(API_PATH + "/deleteStoredPipeline", pipelineName)
    }

    async storePipeline(data) {
        return await this.apiSend(API_PATH + "/storePipeline", data);
    }

    // ---------- Operator Configuration Storage ----------

    async listStoredOperators() {
        return await this.apiSend(API_PATH + "/listStoredOperators")
    }

    async deleteStoredOperator(opPresetName) {
        return await this.apiSend(API_PATH + "/deleteStoredOperator", opPresetName)
    }

    async storeOperator(data) {
        return await this.apiSend(API_PATH + "/storeOperator", data);
    }

    // ---------- -------------------------------- ----------

    async simulate(runtimeConfig, simulateData) {
        this._assureSocket();

        return await this.apiSend(API_PATH + "/simulate", {"runtimeConfig": runtimeConfig, "simulateData": simulateData}).then();
    }

    // --------------------- Compilation ---------------------

    async startCompileMode(data) {
        this._assureSocket();

        return await this.apiSend(API_PATH + "/compileStart", data).then();
    }

    async compileAnalyze(data) {
        this._assureSocket();

        return await this.apiSend(API_PATH + "/compileAnalyze", data).then();
    }

    async compilePipeline(data) {
        this._assureSocket();

        return await this.apiSend(API_PATH + "/compilePipeline", data).then();
    }

    endCompileMode() {
        if(this.socketCon == null) return;  // If we got disconnected no need to end CM

        this.apiSend(API_PATH + "/compileEnd").then();
    }

    // ---------- -------------------------------- ----------

    socketSend(data) {
        this.socketCon.send(JSON.stringify(data))
    }

    async apiSend(url, data) {
        if(data == null) data = {};

        return await axios.post(url, JSON.stringify(data)).then((res) => {
            return res["data"];
        }).catch(function () {
            return null;
        });
    }
}
