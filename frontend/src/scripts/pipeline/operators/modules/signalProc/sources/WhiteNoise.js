import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _WhiteNoise extends Definition {
    constructor(pathIdentifier){
        super("WhiteNoise", "White Noise", pathIdentifier,
            "Generates uniformly distributed white noise audio signals.", true);
    }

    build(operator) {
        let rate = new NumberParam("samplingRate", 44100, 1, null, "Sample Rate", "Number of samples generated per second.");
        let channels = new NumberParam("channels", 1, 1, null, "Channels", "How many channels should be generated.");
        let chunkSize = new NumberParam("chunkSize", 1024, 1, null, "Chunk Size", "Number of frames processed together in one data block / tuple.");

        this._construct(operator,
            [],
            [new SocketDef(signalSocket)],
            [rate, channels, chunkSize], SIGNAL_DT);
    }
}
