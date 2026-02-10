import {Definition} from "@/scripts/pipeline/operators/Definition";
import {STRING_DT, strSocket} from "@/scripts/pipeline/operators/modules/base";
import {anySocket} from "@/scripts/pipeline/operators/modules";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ToInt extends Definition {
    constructor(pathIdentifier){
        super("ToString", "To String", pathIdentifier);
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(strSocket)],
            [], STRING_DT);
    }
}
