import {Definition} from "@/scripts/pipeline/operators/Definition";
import {strSocket} from "@/scripts/pipeline/operators/modules/base";

import {SocketDef} from "@/scripts/pipeline/SvSocket";
import {anySocket} from "@/scripts/pipeline/operators/modules";

export default class _ParseJSON extends Definition {
    constructor(pathIdentifier){
        super("ParseJSON", "Parse JSON", pathIdentifier);
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(strSocket)],
            [new SocketDef(anySocket, "Data")],
            []);
    }
}
