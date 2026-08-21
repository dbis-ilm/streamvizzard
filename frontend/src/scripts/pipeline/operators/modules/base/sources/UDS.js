import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {CodeParam} from "@/scripts/pipeline/operators/modules/base/params/CodeParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _UDS extends Definition {
    constructor(pathIdentifier){
        super("UDS", "User Defined Source", pathIdentifier,
            "User-defined source for custom, stateful data emission handling.", true);
    }

    build(operator) {
        let outCount = new NumberParam("outputs", 1, 1, null, "Outputs");
        let code = new CodeParam("code", CodeParam.CodeType.UDO, "class UserDefinedSource:\n" +
            "    def onStart(self):\n" +
            "        ...\n\n" +
            "    def runLoop(self) -> tuple:\n" +
            "        ...\n\n" +
            "    def onDestroy(self):\n" +
            "        ...");

        this._construct(operator,
            [],
            [new SocketDef(anySocket, "Data")],
            [outCount, code]);
    }

    /** @param {Param} param **/
    onParamChanged(param) {
        // First update sockets & connections (which triggers connection removed)

        if(param.key === "outputs") {
            let op = param.operator;

            this.updateSockets(param.operator, 0, op.getParam("outputs").getValue(),
                new SocketDef(anySocket), new SocketDef(anySocket));

        }
    }

    /** @param {SvOperator} operator
     * @param {Object} data **/
    setParamData(operator, data) {
        super.setParamData(operator, data);

        this.updateSockets(operator, 0, operator.getParam("outputs").getValue(),
            new SocketDef(anySocket), new SocketDef(anySocket));
    }
}
