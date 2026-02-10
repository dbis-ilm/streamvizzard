import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {anySocket} from "@/scripts/pipeline/operators/modules";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Combine extends Definition {
    constructor(pathIdentifier){
        super("Combine", "Combine", pathIdentifier);
    }

    build(operator) {
        let ins = new NumberParam("ins", 1,0, null, "Inputs");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(anySocket)],
            [ins]
        );
    }

    /** @param {Param} param **/
    onParamChanged(param) {
        this.updateSockets(param.operator, param.getValue(), 1, new SocketDef(anySocket), new SocketDef(anySocket));
    }

    /** @param {SvOperator} operator
     * @param {Object} data **/
    setParamData(operator, data) {
        super.setParamData(operator, data);

        this.updateSockets(operator, operator.getParam("ins").getValue(), 1, new SocketDef(anySocket), new SocketDef(anySocket));
    }
}
