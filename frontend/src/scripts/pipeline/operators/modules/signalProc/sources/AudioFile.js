import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {BoolParam} from "@/scripts/pipeline/operators/modules/base/params/BoolParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _AudioFile extends Definition {
    constructor(pathIdentifier){
        super("AudioFile", "Audio File", pathIdentifier, true);
    }

    build(operator) {
        let path = new StringParam("path", "", "Source");
        let rate = new NumberParam("rate", 44100, 1, null, "Sample Rate");
        let repeat = new BoolParam("repeat",  false, "Loop",
            "Repeats from the start when reaching end of file");

        this._construct(operator,
            [],
            [new SocketDef(signalSocket)],
            [path, rate, repeat], SIGNAL_DT);
    }
}
