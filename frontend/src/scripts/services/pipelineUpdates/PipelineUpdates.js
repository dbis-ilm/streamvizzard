class PipelineUpdate {
    createSocketData() { return {}; }

    checkUpdate() { return false; }

    // If the structure or params of the pipeline is changed
    changesSemantic() { return true; }
}

export class OperatorAddedPU extends PipelineUpdate {
    constructor(opID, opData) {
        super();

        this.opID = opID;
        this.opData = opData;
    }

    createSocketData() {
        return { type: "opAdded", opID: this.opID, opData: this.opData };
    }

    checkUpdate(other) {
        if(other instanceof OperatorAddedPU && other.opID === this.opID) {
            this.opID = other.opID;
            this.opData = other.opData;

            return true;
        }

        return false;
    }
}

export class OperatorRemovedPU extends PipelineUpdate {
    constructor(opID) {
        super();

        this.opID = opID;
    }

    createSocketData() {
        return { type: "opRemoved", opID: this.opID };
    }

    checkUpdate(other) {
        return other instanceof OperatorRemovedPU && other.opID === this.opID;
    }
}

export class OperatorParamsUpdatedPU extends PipelineUpdate {
    constructor(opID, opData, param) {
        super();

        this.opID = opID;
        this.opData = opData;
        this.param = param;
    }

    createSocketData() {
        return { type: "opParamsUpdated", opID: this.opID, opData: this.opData, param: this.param };
    }

    checkUpdate(other) {
        if(other instanceof OperatorParamsUpdatedPU && other.opID === this.opID
            && other.param === this.param) {
            this.opID = other.opID;
            this.opData = other.opData;
            this.param = other.param;

            return true;
        }

        return false;
    }
}

export class OperatorConfigUpdatedPU extends PipelineUpdate {
    constructor(opID, metaData) {
        super();

        this.opID = opID;
        this.metaData = metaData;
    }

    createSocketData() {
        return { type: "opConfigUpdated", opID: this.opID, metaData: this.metaData };
    }

    checkUpdate(other) {
        if(other instanceof OperatorConfigUpdatedPU && other.opID === this.opID) {
            this.opID = other.opID;
            this.metaData = other.metaData;

            return true;
        }

        return false;
    }

    changesSemantic() { return false; }
}

export class ConnectionAddedPU extends PipelineUpdate {
    /** @param {SvConnection} con **/
    constructor(con) {
        super();

        this.connectionID = con.id;
        this.outOpID = con.output.operator.id;
        this.inOpID = con.input.operator.id;
        this.outSocketID = con.output.id;
        this.inSocketID = con.input.id;
    }

    createSocketData() {
        return {
            type: "conAdded",
            connectionID: this.connectionID,
            outOpID: this.outOpID,
            inOpID: this.inOpID,
            outSocketID: this.outSocketID,
            inSocketID: this.inSocketID
        };
    }

    checkUpdate(other) {
        if(other instanceof ConnectionAddedPU && other.connectionID === this.connectionID) {
            this.connectionID = other.connectionID;
            this.outOpID = other.outOpID;
            this.inOpID = other.inOpID;
            this.outSocketID = other.outSocketID;
            this.inSocketID = other.inSocketID;

            return true;
        }

        return false;
    }
}

export class ConnectionRemovedPU extends PipelineUpdate {
    constructor(connectionID) {
        super();

        this.connectionID = connectionID;
    }

    createSocketData() {
        return { type: "conRemoved", connectionID: this.connectionID };
    }

    checkUpdate(other) {
        return other instanceof ConnectionRemovedPU && other.connectionID === this.connectionID;
    }
}

export class GenericUpdatePU extends PipelineUpdate {
    checkUpdate(other) {
        return other instanceof GenericUpdatePU;
    }

    createSocketData() {
        return { type: "generic" };
    }

    changesSemantic() { return false; }
}
