import {Definition} from "@/scripts/pipeline/operators/Definition";
import {BoolParam} from "@/scripts/pipeline/operators/modules/base/params/BoolParam";
import {STRING_DT, strSocket} from "@/scripts/pipeline/operators/modules/base";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _TextFile extends Definition {
    constructor(pathIdentifier){
        super("TextFile", "Text File", pathIdentifier,
            "Reads elements line-by-line from a text file and streams them into the pipeline.", true);
    }

    build(operator) {
        let repeat = new BoolParam("repeat", false, "Loop", "Repeats from the start when reaching end of file");
        let path = new StringParam("path", "", "Path");
        let limitRate = new BoolParam("limitRate", true, "Limit Rate",
            "If the source should produce tuples in a fixed rate");
        let rate = new NumberParam("rate", 30, 0, null,
            "Rate","How many lines per second are processed");

        limitRate.onChangeCallback = (val) => { rate.show = val; };

        this._construct(operator,
            [],
            [new SocketDef(strSocket, "Data")],
            [repeat, path, limitRate, rate], STRING_DT);
    }
}
