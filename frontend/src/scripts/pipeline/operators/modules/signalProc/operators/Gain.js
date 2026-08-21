import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Gain extends Definition {
    constructor(pathIdentifier){
        super("Gain", "Gain", pathIdentifier,
            "Scales signal amplitude by applying a constant gain factor.");
    }

    build(operator) {
        let gain= new NumberParam("gain", 1, null, null, "Gain");

        this._construct(operator,
            [new SocketDef(signalSocket)],
            [new SocketDef(signalSocket)],
            [gain], SIGNAL_DT);
    }
}
