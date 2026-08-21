import {Definition} from "@/scripts/pipeline/operators/Definition";
import {STRING_DT} from "@/scripts/pipeline/operators/modules/base";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {CodeParam} from "@/scripts/pipeline/operators/modules/base/params/CodeParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _UDO extends Definition {
    constructor(pathIdentifier){
        super("UDO", "User Defined Operator", pathIdentifier,
            "User-defined operator for custom, stateful input tuple handling.");
    }

    build(operator) {
        let inCount = new NumberParam("inputs", 1,0, null, "Inputs");
        let outCount = new NumberParam("outputs", 1, 0, null, "Outputs");
        let code = new CodeParam("code", CodeParam.CodeType.UDO,
        "class UserDefinedOperator:\n" +
            "    def onStart(self):\n" +
            "        ...\n\n" +
            "    def execute(self, tupleIn: Tuple) -> tuple:\n" +
            "        return tupleIn.data\n\n" +
            "    def onDestroy(self):\n" +
            "        ...");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(anySocket)],
            [inCount, outCount, code], STRING_DT);
    }

    /** @param {Param} param **/
    onParamChanged(param) {
        // First update sockets & connections (which triggers connection removed)

        if(param.key === "inputs" || param.key === "outputs") {
            let op = param.operator;

            this.updateSockets(param.operator, op.getParam("inputs").getValue(), op.getParam("outputs").getValue(),
                new SocketDef(anySocket), new SocketDef(anySocket));

        }
    }

    /** @param {SvOperator} operator
     * @param {Object} data **/
    setParamData(operator, data) {
        super.setParamData(operator, data);

        this.updateSockets(operator, operator.getParam("inputs").getValue(), operator.getParam("outputs").getValue(),
            new SocketDef(anySocket), new SocketDef(anySocket));
    }
}
