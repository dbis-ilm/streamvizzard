import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _MissingValues extends Definition {
    constructor(pathIdentifier){
        super("MissingValues", "Missing Values", pathIdentifier);
    }

    build(operator) {
        let mode = new SelectParam("mode",
            [{title: "Linear", key: "linear"},
                {title: "Polynomial", key: "polynomial"},
                {title: "Padding", key: "padding"},
                {title: "Drop", key: "drop"},],
            "linear", "Replacement");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(anySocket, "Cleaned")],
            [mode]);
    }
}
