import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";
import {signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

export default class _CombineChannels extends Definition {
    constructor(pathIdentifier){
        super("CombineChannels", "Combine Channels", pathIdentifier,
            "Combines the channel data of all input signals into one resulting output signal. All input signals must have matching sampling rates and sample counts!");
    }

    build(operator) {
        let ins = new NumberParam("ins", 2,1, null, "Inputs");

        this._construct(operator,
            [new SocketDef(signalSocket), new SocketDef(signalSocket)],
            [new SocketDef(signalSocket)],
            [ins]
        );
    }

    /** @param {Param} param **/
    onParamChanged(param) {
        this.updateSockets(param.operator, param.getValue(), 1, new SocketDef(signalSocket), new SocketDef(signalSocket));
    }

    /** @param {SvOperator} operator
     * @param {Object} data **/
    setParamData(operator, data) {
        super.setParamData(operator, data);

        this.updateSockets(operator, operator.getParam("ins").getValue(), 1, new SocketDef(signalSocket), new SocketDef(signalSocket));
    }
}
