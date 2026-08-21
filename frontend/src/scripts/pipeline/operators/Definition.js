import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";

/** Static singleton class, all operators share the same definition instance **/
export class Definition {
    constructor(internalName, displayName, pathIdentifier, description, source=false){
        // The internal name should be the same as the class name in backend
        // to allow generating UI saveFiles from the backend pipeline!

        this.displayName = displayName
        this.identifier = internalName;
        this.path = pathIdentifier;
        this.description = description;
        this.source = source;
        this.contextPath = null;
        this.bgColor = null;
    }

    /** @param {SvOperator} operator **/
    build(operator) {
        console.error("Builder method not implemented for", operator);
    }

    /** @param {SvOperator} operator The operator instance to build
     * @param {Array<SocketDef>} inputs
     * @param {Array<SocketDef>} outputs
     * @param {Array<Param>} params
     * @param {MonitorDataType|null} dataDisplayType **/
    _construct(operator, inputs, outputs, params, dataDisplayType=null) {
        for (let i in inputs) operator.createSocket(inputs[i], true);

        for (let param of params) operator.addParameter(param);

        for (let i in outputs) operator.createSocket(outputs[i], false);

        operator.monitor.updateDisplayDataType(dataDisplayType);
    }

    onParamChanged(param) {
        void param;
    }

    /** @param {SvOperator} operator
     * @param {Number} socksIn
     * @param {Number} socksOut
     * @param {SocketDef} inDef
     * @param {SocketDef} outDef **/
    updateSockets(operator, socksIn, socksOut, inDef, outDef) {
        // Remove / add desired sockets

        let currentInCount = operator.inputs.length;
        let currentOutCount = operator.outputs.length;

        if(socksIn >= currentInCount) for (let i = currentInCount; i < socksIn; i++) operator.createSocket(inDef, true);
        else for (let i = currentInCount - 1; i >= socksIn; i--) {
            let socket = operator.inputs[i];

            operator.removeSocket(socket);
        }

        if(socksOut >= currentOutCount) for (let i = currentOutCount; i < socksOut; i++) operator.createSocket(outDef, false);
        else for (let i = currentOutCount - 1; i >= socksOut; i--) {
            let socket = operator.outputs[i];

            operator.removeSocket(socket);
        }

        executeEvent(EVENTS.OP_SOCKET_COUNT_CHANGED, operator);
    }

    getFullPath() {
        let path = "";

        for(let v = 0; v < this.path.length; v++) {
            if(v > 0) path += "/";
            path += this.path[v];
        }

        path += "/" + this.identifier;

        return path;
    }

    /** @param {SvOperator} operator
     * @param {Object} data **/
    setParamData(operator, data) {
        for(let param of operator.params) {
            if(param.key in data) param.setValue(data[param.key]);
        }
    }
}
