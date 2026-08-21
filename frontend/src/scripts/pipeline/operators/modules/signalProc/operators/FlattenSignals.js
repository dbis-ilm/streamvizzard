import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _FlattenSignals extends Definition {
    constructor(pathIdentifier){
        super("FlattenSignals", "Flatten Signals", pathIdentifier,
            "Merges an input list of signals into one combined signal.");
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(anySocket, "Signals")],
            [new SocketDef(signalSocket)],
            [], SIGNAL_DT);
    }
}
