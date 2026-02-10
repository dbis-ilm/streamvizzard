import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Bandpass extends Definition {
    constructor(pathIdentifier){
        super("Bandpass", "Bandpass", pathIdentifier);
    }

    build(operator) {
        let threshold1 = new NumberParam("threshold1", 100, 1, null, "Threshold 1");
        let threshold2 = new NumberParam("threshold2", 200, 1, null, "Threshold 2");
        let order= new NumberParam("order", 3, 1, null, "Order");

        this._construct(operator,
            [new SocketDef(signalSocket)],
            [new SocketDef(signalSocket)],
            [threshold1, threshold2, order], SIGNAL_DT);
    }
}
