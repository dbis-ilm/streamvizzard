import {Definition} from "@/scripts/pipeline/operators/Definition";
import {SIGNAL_DT, signalSocket} from "@/scripts/pipeline/operators/modules/signalProc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";

export default class _ExtractChannels extends Definition {
    constructor(pathIdentifier){
        super("ExtractChannels", "Extract Channels", pathIdentifier,
            "Extracts individual channels from an input signal and returns a signal containing all specified channels.");
    }

    build(operator) {
        let channels= new StringParam("channels", "1", "Channels", "The channels to extract, allows comma separated individual channels and ranges: 1,2,4-6,9");

        this._construct(operator,
            [new SocketDef(signalSocket)],
            [new SocketDef(signalSocket)],
            [channels], SIGNAL_DT);
    }
}
