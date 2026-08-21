import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Highpass extends Definition {
    constructor(pathIdentifier){
        super("Highpass", "Highpass", pathIdentifier,
            "Filters an input signal and keeps only frequencies above the threshold.");
    }

    build(operator) {
        let threshold= new NumberParam("threshold", 1000, 1, null, "Threshold");
        let order= new NumberParam("order", 3, 1, null, "Order");

        this._construct(operator,
            [new SocketDef(signalSocket)],
            [new SocketDef(signalSocket)],
            [threshold, order], SIGNAL_DT);
    }
}
