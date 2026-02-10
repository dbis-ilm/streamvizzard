import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Microphone extends Definition {
    constructor(pathIdentifier){
        super("Microphone", "Microphone", pathIdentifier, true);
    }

    build(operator) {
        let rate = new NumberParam("rate", 44100, 1, null, "Rate")

        this._construct(operator,
            [],
            [new SocketDef(signalSocket)],
            [rate], SIGNAL_DT);
    }
}
