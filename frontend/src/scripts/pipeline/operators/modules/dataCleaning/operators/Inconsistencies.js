import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Inconsistencies extends Definition {
    constructor(pathIdentifier){
        super("Inconsistencies", "Inconsistencies", pathIdentifier,
            "Detects inconsistencies in the input data (list of numerical elements) and potentially resolves them.");
    }

    build(operator) {
        let threshold = new NumberParam("threshold", -100, null, null, "Threshold");
        let maxValue = new NumberParam("maxValue", 1000, null, null, "Max. Value");
        let mode = new SelectParam("mode",
            [{title: "Mean", key: "mean"}, {title: "Mode", key: "mode"},
                {title: "Median", key: "median"}, {title: "Remove", key: "remove"}],
            "mean", "Replacement");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(anySocket, "Cleaned"), new SocketDef(anySocket, "Invalid")],
            [threshold, maxValue, mode]);
    }
}
