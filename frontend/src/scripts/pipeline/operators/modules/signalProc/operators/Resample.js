import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Resample extends Definition {
    constructor(pathIdentifier){
        super("Resample", "Resample", pathIdentifier);
    }

    build(operator) {
        let sampleRate= new NumberParam("sampleRate", 16000, 1, null, "Sample Rate");

        this._construct(operator,
            [new SocketDef(signalSocket)],
            [new SocketDef(signalSocket)],
            [sampleRate], SIGNAL_DT);
    }
}
