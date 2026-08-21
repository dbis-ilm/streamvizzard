import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _NotchFilter extends Definition {
    constructor(pathIdentifier){
        super("NotchFilter", "Notch Filter", pathIdentifier,
            "Removes a narrow frequency band from a signal while preserving frequencies outside the rejected range.");
    }

    build(operator) {
        let frequency= new NumberParam("frequency", 1000, 1, null, "Frequency");
        let quality= new NumberParam("quality", 30, 1, null, "Quality",
            "High value indicates a narrow notch while lower value results in removing larger portions of adjacent frequencies.");

        this._construct(operator,
            [new SocketDef(signalSocket)],
            [new SocketDef(signalSocket)],
            [frequency, quality], SIGNAL_DT);
    }
}
