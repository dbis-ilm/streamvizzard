import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {CodeParam} from "@/scripts/pipeline/operators/modules/base/params/CodeParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _UDF extends Definition {
    constructor(pathIdentifier){
        super("Filter", "Filter", pathIdentifier,
            "Filter out specific input tuples based on a user-defined function (return true for keeping the tuples).");
    }

    build(operator) {
        let code = new CodeParam("code", CodeParam.CodeType.FILTER, "return input[0] is not None");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(anySocket)],
            [code]);
    }
}
