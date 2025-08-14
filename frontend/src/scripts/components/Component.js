import Rete from "rete";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import {v4} from 'uuid';

export class Component extends Rete.Component {
    constructor(internalName, displayName, pathIdentifier, source=false){
        // The internal name should be the same as the class name in backend
        // to allow generating UI saveFiles from the backend pipeline!
        super(internalName);

        this.displayName = displayName
        this.identifier = internalName;
        this.path = pathIdentifier;
        this.source = source;
    }

    onBuilderInitialized(node, display, inputs, outputs, controls) {
        node.viewName = this.displayName;
        node.uuid = v4();  // ID unique for this operator, persistent across parameter changes

        for (let i in inputs) {
            const inpData = inputs[i];
            let sock = new Rete.Input('in' + i,inpData.name, inpData.socket);
            sock.defaultName = sock.name;
            node.addInput(sock);
        }

        node.display = display;
        if(display != null) {
            display.dataMonitor = true;
            node.addControl(display);
        }

        for (let control of controls) node.addControl(control);

        for (let i in outputs) {
            const outData = outputs[i];

            let sock = new Rete.Output('out' + i,outData.name, outData.socket);
            sock.defaultName = sock.name;
            node.addOutput(sock);
        }

        this.editor.onComponentCreated(node, this);

        return node;
    }

    onControlValueChanged(ctrl, node, oldVal) {
        ctrl.onValueChanged();

        node.component.editor.onOperatorDataUpdated(node, ctrl);

        executeEvent(EVENTS.NODE_PARAM_CHANGED, [node, ctrl, oldVal]);
    }

    updateVisuals(node) {
        node.update();
        this.updateConnections(node);
    }

    updateConnections(node) {
        node.component.editor.view.updateConnections({ node: node });
    }

    onSocketsChanged(node) {
        if(node.display != null) node.display.onSocketsChanged(node);
    }

    sendMetaDataUpdate(node) {
        node.component.editor.onOperatorMetaUpdated(node);
    }

    setDataMonitorState(node, enabled, trigger = true) {
        node.dataMonitorEnabled = enabled;

        this.updateConnections(node);

        if(trigger) node.component.editor.trigger("nodeMonitorStateChanged", {"node": node, "state": enabled});

        node.component.sendMetaDataUpdate(node);
    }

    setOperatorSettingsState(node, show) {
        node.settingsEnabled = show;

        node.component.updateConnections(node);
    }

    async updateSockets(node, socksIn, socksOut, inType, outType) {
        // Backup old connections

        const cIn = [];
        const cOut = [];

        for (const [, v] of node.inputs.entries()) {
            for (const con of v.connections) {
                cIn.push({
                    sockIn: v.key,
                    sockOut: con.output.key,
                    nodeIn: node,
                    nodeOut: con.output.node
                });

                node.component.editor.removeConnection(con);
            }

            node.removeInput(v);
        }

        for (const [, v] of node.outputs.entries()) {
            for (const con of v.connections) {
                cOut.push({
                    sockIn: con.input.key,
                    sockOut: v.key,
                    nodeIn: con.input.node,
                    nodeOut: node
                });

                node.component.editor.removeConnection(con);
            }

            node.removeOutput(v);
        }

        // Create Sockets

        //TODO: MAYBE ASSIGN DATA TYPES OR NAME SOCKETS?
        for (let i = 0; i < socksIn; i++) node.addInput(new Rete.Input('in' + i, inType.name, inType))
        for (let i = 0; i < socksOut; i++) node.addOutput(new Rete.Output('out' + i, outType.name, outType))

        this.onSocketsChanged(node);

        await node.update();

        //Reapply old connections

        for(let e of cIn) {
            if(!e.nodeIn.inputs.has(e.sockIn)) continue;
            node.component.editor.connect(e.nodeOut.outputs.get(e.sockOut), e.nodeIn.inputs.get(e.sockIn));
        }

        for(let e of cOut) {
            if(!e.nodeOut.outputs.has(e.sockOut)) continue;
            node.component.editor.connect(e.nodeOut.outputs.get(e.sockOut), e.nodeIn.inputs.get(e.sockIn));
        }

        await node.update();
    }

    getID(node) {
        let path = "";

        for(let v = 0; v < this.path.length; v++) {
            if(v > 0) path += "/";
            path += this.path[v];
        }

        path += "/" + this.identifier;

        return {
            id: node.id,
            path: path,
            uuid: node.uuid
        };
    }

    getPipelineData(node){
        return {
            id: node.component.getID(node),
            inputs: node.component.getInputs(node),
            outputs: node.component.getOutputs(node),
            data: node.component.getData(node),
            monitor: node.component.getMonitorData(node),
            breakpoints: node.component.getBreakpoints(node)
        };
    }

    getMetaData(node) {
        return {
            monitor: node.component.getMonitorData(node),
            breakpoints: node.component.getBreakpoints(node)
        }
    }

    getINSocketByKey(node, key) {
        let idx = 0;

        for (const [k,] of node.inputs.entries()) {
            if(k === key) return idx;

            idx++;
        }

        return -1;
    }

    getOUTSocketByKey(node, key) {
        let idx = 0;

        for (const [k,] of node.outputs.entries()) {
            if(k === key) return idx;

            idx++;
        }

        return -1;
    }

    getSocketByKey(node, key) {
        if(node.inputs.has(key)) return node.inputs.get(key);
        else if(node.outputs.has(key)) return node.outputs.get(key);
        return null;
    }

    getInputs(node) {
        const ins = [];

        let idx = 0;

        for (const [, v] of node.inputs.entries()) {
            const _in = {
                socket: idx,
                connected: []
            }

            if(v.connections.length > 1) console.error("ONLY ONE INPUT ALLOWED FOR: " + v);

            for(const c of v.connections) {
                const otherOp = c.output.node.component;  //Our component is the input of the connection
                _in.connected.push({
                    socket: otherOp.getOUTSocketByKey(c.output.node, c.output.key), //The key of the OUTPUT of the other component
                    component: otherOp.getID(c.output.node),
                    id: c.id
                });

                break; //Only one input allowed!
            }

            ins.push(_in);

            idx++;
        }

        return ins;
    }

    getOutputs(node) {
        const outs = [];

        let idx = 0;

        for (const [, v] of node.outputs.entries()) {
            const out = {
                socket: idx,
                connected: []
            };

            for(const c of v.connections) {
                const otherOp = c.input.node.component; //Our component is the output of the connection

                out.connected.push({
                    socket: otherOp.getINSocketByKey(c.input.node, c.input.key), //The key of the INPUT of the other component
                    component: otherOp.getID(c.input.node),
                    id: c.id
                });
            }

            outs.push(out);

            idx++;
        }

        return outs;
    }

    clearAllConnections(node) {
        for (const [, v] of node.inputs.entries()) {
            for(const con of v.connections) node.component.editor.removeConnection(con);
        }

        for (const [, v] of node.outputs.entries()) {
            for(const con of v.connections) node.component.editor.removeConnection(con);
        }
    }

    getMonitorData(node) {
        return {
            state: {
                sendData: node.dataMonitorEnabled,
            },
            dMode: node.display != null ? node.display.getDisplayData() : null
        };
    }

    setMonitorData(node, data) {
        if(node.display != null) node.display.setDisplayData(data.dMode);

        this.setDataMonitorState(node, data.state.sendData, true); //TODO: COMBINE THIS TWO FUNCTIONS?
    }

    getBreakpoints(node) {
        return node.vueContext.breakPoints;
    }

    setBreakpoints(node, bps) {
        node.vueContext.updateBreakpoints(bps);
    }

    setHeatmapRating(node, rating) {
        node.vueContext.heatmapRating = rating;
    }

    setAdvisorSuggestions(node, suggestions) {
        node.vueContext.updateAdvisorSuggestion(suggestions);
    }

    setError(node, error) {
        node.vueContext.updateError(error);
    }

    setMessageBrokerState(node, broker) {
        node.vueContext.updateMessageBroker(broker);
    }

    setValue(node, data) {
        if(node.display != null) node.display.setData(data);
    }

    async setData(node, data) {
        for(let ctrl of node.controls) {
            let obj = ctrl[1];
            if(obj.dataMonitor) continue;

            if(obj.key in data) obj.setValue(data[obj.key]);
        }
    }

    getData(node) {
        let data = {};

        // Collect all values from all controls (except dataMonitor)

        for(let ctrl of node.controls) {
            let obj = ctrl[1];
            if(obj.dataMonitor) continue;

            data[obj.key] = obj.getValue();
        }

        return data;
    }

    reset(node, nodeData=true, displayData=true) {
        if(node.display != null && displayData) node.display.reset();
        if(nodeData) node.vueContext.reset();
    }
}
