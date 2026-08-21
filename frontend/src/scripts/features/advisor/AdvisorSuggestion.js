import {SvInstance} from "@/scripts/StreamVizzard";

/** @param {Object} rawData
 * @returns {AdvisorSuggestion|null} */
export function parseAdvisorSuggestion(rawData) {
    let type = rawData["type"];

    if(type === "AddOp") return new AddOpAS(rawData["msg"], rawData["ops"], rawData["socket"]);
    else if(type === "AdjParam") return new AdjustParamAS(rawData["msg"], rawData["params"]);

    return null;
}

class AdvisorSuggestion {
    /** @param {String|null} message */
    constructor(message) {
        this.message = message;
    }
}

export class AddOpAS extends AdvisorSuggestion {
    /** @param {String|null} message
     * @param {Array<{name: String, path: String, params: Object<String, Object>}>} ops
     * @param {{in: Boolean, id: Number}} socket */
    constructor(message, ops, socket) {
        super(message);

        this.ops = ops;
        this.socket = socket;
    }

    /** @param {{name: String, path: String, params: Object<String, Object>}} selectedOp
     * @param {SvOperator} sourceOp */
    async apply(selectedOp, sourceOp) {
        // Find selected operator by path

        let def = SvInstance.modules.getOperatorDefinition(selectedOp.path);

        if(def == null) return;

        // Instantiate operator

        let xPos = this.socket.in ? sourceOp.posX - 60 : sourceOp.width - 60;

        let op = await SvInstance.pipeline.createOperator(def, {x: xPos, y: sourceOp.posY + 60});
        if(op == null) return;

        SvInstance.editor.selectEditorObject(op);

        // Setup potential parameters

        for(let paramKey in selectedOp.params) {
            let param = op.getParam(paramKey);
            if(param != null) param.setValue(selectedOp.params[paramKey]);
        }

        // Connect new operator

        let targetSocket = sourceOp.getSocketByID(this.socket.id, this.socket.in);
        if(targetSocket == null) return;

        if(targetSocket.input) {
            let conToReplace = targetSocket.connections.at(0);
            if(conToReplace == null) return;

            // Remove orig con
            SvInstance.pipeline.deleteConnection(conToReplace);

            // Connect new op to sourceOp [PrevInOp -> NewOp ##->## SourceOp]
            SvInstance.pipeline.createConnection(targetSocket, op.getSocketByID(0, false));

            // Connect prev IN neighbour of sourceOp to newOp [PrevInOp ##->## NewOp -> SourceOp]
            SvInstance.pipeline.createConnection(conToReplace.output, op.getSocketByID(0, true));
        } else {
            let consToReplace = targetSocket.connections.slice(); // Shallow copy

            for(let conToReplace of consToReplace) {
                // Remove orig con
                SvInstance.pipeline.deleteConnection(conToReplace);

                // Connect new op to sourceOp [SourceOp ##->## NewOp -> PrevOutOp]
                SvInstance.pipeline.createConnection(op.getSocketByID(0, true), targetSocket);

                // Connect prev OUT neighbour of sourceOp to newOp [SourceOp -> NewOp ##->## PrevOutOp]
                SvInstance.pipeline.createConnection(op.getSocketByID(0, false), conToReplace.input);
            }
        }
    }
}

export class AdjustParamAS extends AdvisorSuggestion {
    /** @param {String|null} message
     * @param {Object<String, Object>} params */
    constructor(message, params) {
        super(message);

        this.params = params;
    }

    /** @param {SvOperator} sourceOp */
    apply(sourceOp) {
        for(let paramKey in this.params) {
            let param = sourceOp.getParam(paramKey);
            if(param != null) param.setValue(this.params[paramKey]);
        }
    }
}
