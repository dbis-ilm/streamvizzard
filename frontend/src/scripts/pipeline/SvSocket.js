import {safeVal, valueOr} from "@/scripts/tools/Utils";
import {SvInstance} from "@/scripts/StreamVizzard";
import TemplateHost from "@/scripts/tools/TemplateHost";
import {ViewConnector} from "@/scripts/tools/ViewConnector";
import {anySocket} from "@/scripts/pipeline/operators/modules";

export class SocketType {
    /** @param {String} name **/
    constructor(name) {
        this.name = name;

        this.compatibleTypes = new Set();
    }

    /** @param {SocketType} other */
    compatibleWith(other) {
        this.compatibleTypes.add(other);
        other.compatibleTypes.add(this);
    }

    /** @param {SocketType} other
     * @returns Boolean */
    isCompatibleWith(other) {
        // Always compatible with same type and with anySocket
        if(this === other || this === anySocket || other === anySocket) return true;

        return this.compatibleTypes.has(other);
    }
}

export class SocketDef {
    /** @param {SocketType} type
     * @param {String|null} name **/
    constructor(type, name = null) {
        this.type = type;
        this.name = name;
    }

    getDisplayName() {
        return valueOr(this.name, this.type.name);
    }
}

export default class SvSocket extends TemplateHost {
    /** @param {SvOperator} operator
     * @param {SocketDef} definition
     * @param {Number} id
     * @param {Boolean} input
     * @param {String|null} name **/
    constructor(operator, definition, id, input, name) {
        super();

        this.operator = operator;

        this.definition = definition;

        this.id = id;
        this.input = input; // If socket is input socket

        this.name = name != null ? name : this.getDefaultName();

        /** @type Array<SvConnection> **/
        this.connections = [];

        this.viewConnector = new ViewConnector();
    }

    /** @return {{x: number, y: number}} **/
    getPosition() {
        let dimensions = this.viewConnector.request("dimensions");

        let posInView = SvInstance.editor.getEditorPos({
            x: dimensions.x + dimensions.width / 2,
            y: dimensions.y + dimensions.height / 2
        });

        return {x: posInView.x, y: posInView.y};
    }

    getSize() {
        let dimensions = this.viewConnector.request("dimensions");

        return Math.max(dimensions.width, dimensions.height);
    }

    getDefaultName() {
        return this.definition.getDisplayName();
    }

    /** @param {SvConnection} connection**/
    addConnection(connection) {
        if(connection in this.connections) return false; // Already present

        // Clear previous connections if it is an input socket

        if(this.input) this.clearConnections();

        this.connections.push(connection);

        if(this.input) connection.input = this;
        else connection.output = this;

        return true;
    }

    /** @param {SvConnection} connection**/
    removeConnection(connection) {
        let idx = this.connections.indexOf(connection);

        if(idx > -1) this.connections.splice(idx, 1);

        // Connection keeps its reference to this socket for event purposes
    }

    clearConnections() {
        for(let con of this.connections) SvInstance.pipeline.deleteConnection(con);
    }

    // ----------------------------------------------------- Storage ---------------------------------------------------

    exportSaveData() {
        return {"id": this.id, "name": this.name}
    }

    importSaveData(data) {
        // Don't import id in case it was changed during socket creation!

        this.name = safeVal(data["name"], this.name);
    }
}