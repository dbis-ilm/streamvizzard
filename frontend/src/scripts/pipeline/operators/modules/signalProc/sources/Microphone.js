import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Microphone extends Definition {
    constructor(pathIdentifier){
        super("Microphone", "Microphone", pathIdentifier,
            "Streams recorded audio signals captured by an connected device into the pipeline.", true);
    }

    build(operator) {
        let rate = new NumberParam("rate", 44100, 1, null, "Rate", "Number of times per second the microphone measures the sound signal, which determines how accurately high frequencies can be captured.");
        let chunkSize = new NumberParam("chunkSize", 1024, 1, null, "Chunk Size", "Number of frames processed together in one data block / tuple.");

        this._construct(operator,
            [],
            [new SocketDef(signalSocket)],
            [rate, chunkSize], SIGNAL_DT);
    }
}
