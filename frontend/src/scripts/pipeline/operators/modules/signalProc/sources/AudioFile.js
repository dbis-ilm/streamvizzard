import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {BoolParam} from "@/scripts/pipeline/operators/modules/base/params/BoolParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _AudioFile extends Definition {
    constructor(pathIdentifier){
        super("AudioFile", "Audio File", pathIdentifier,
            "Loads an input audio file and streams the individual frames into the pipeline.", true);
    }

    build(operator) {
        let path = new StringParam("path", "", "Source");
        let rate = new NumberParam("rate", 44100, 1, null, "Sample Rate", "Number of times per second the microphone measures the sound signal, which determines how accurately high frequencies can be captured.");
        let chunkSize = new NumberParam("chunkSize", 1024, 1, null, "Chunk Size", "Number of frames processed together in one data block / tuple.");
        let repeat = new BoolParam("repeat",  false, "Loop",
            "Repeats from the start when reaching end of file");

        this._construct(operator,
            [],
            [new SocketDef(signalSocket)],
            [path, rate, chunkSize, repeat], SIGNAL_DT);
    }
}
