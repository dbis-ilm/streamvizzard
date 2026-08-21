import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";

export default class _Resample extends Definition {
    constructor(pathIdentifier){
        super("Resample", "Resample", pathIdentifier,
            "Resamples the input signal.");
    }

    build(operator) {
        let sampleRate= new NumberParam("sampleRate", 16000, 1, null, "Sample Rate");
        let mode = new SelectParam("mode",
            [{title: "FFT", key: 0}, {title: "Polyphase", key: 1}, {title: "Decimate", key: 2}], 0, "Mode",
            "FFT: FFT-based, ensures exact sample size, may produce aliasing | Polyphase = Polyphase FIR filtering, good antialiasing | Decimate = Anti-alias filter + downsampling");

        this._construct(operator,
            [new SocketDef(signalSocket)],
            [new SocketDef(signalSocket)],
            [mode, sampleRate], SIGNAL_DT);
    }
}
